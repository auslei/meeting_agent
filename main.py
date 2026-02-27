import time
import os
from src.common.logger import agent_logger as logger
from src.common.gui_interactor import GUIInteractor
from src.wechat.watcher import WeChatWatcher
from src.wemeet.joiner import WeMeetJoiner
from src.common.audio_recorder import AudioRecorder

# Configuration
POLL_INTERVAL = 10 
RECORDINGS_DIR = "recordings"
HISTORY_FILE = "joined_meetings.log"

os.makedirs(RECORDINGS_DIR, exist_ok=True)

class MeetingAgent:
    """
    Main agent that orchestrates WeChat monitoring, WeMeet joining,
    and audio recording.
    """
    def __init__(self):
        self.interactor = GUIInteractor()
        self.watcher = WeChatWatcher(self.interactor)
        self.joiner = WeMeetJoiner(self.interactor)
        self.recorder = AudioRecorder()
        self.in_meeting = False
        self.joined_history = self._load_history()

    def _load_history(self) -> set:
        """Load joined meeting IDs from history file."""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _save_to_history(self, meeting_id: str):
        """Save a joined meeting ID to the history file."""
        self.joined_history.add(meeting_id)
        with open(HISTORY_FILE, "a") as f:
            f.write(f"{meeting_id}\n")

    def run(self) -> None:
        logger.info("Starting Meeting Agent...")
        
        for event in self.watcher.watch(POLL_INTERVAL):
            meeting_id = event["value"]

            if self.in_meeting:
                logger.info(f"Already in a meeting. Ignoring: {meeting_id}")
                continue
            
            if meeting_id in self.joined_history:
                logger.debug(f"Meeting {meeting_id} already joined in the past. Skipping.")
                continue

            logger.info(f"Detected new meeting: {meeting_id}. Attempting to join...")
            
            success = self.joiner.join_via_scheme(meeting_id)
            if not success:
                logger.warning(f"Failed via scheme. Trying GUI fallback...")
                success = self.joiner.join_via_gui(meeting_id)
            
            if success:
                self.in_meeting = True
                self._save_to_history(meeting_id)
                logger.info(f"Successfully joined meeting {meeting_id}. Starting recording...")
                
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(RECORDINGS_DIR, f"meeting_{meeting_id}_{timestamp}.mp3")
                
                try:
                    self.recorder.start()
                    self.monitor_meeting(output_path)
                except Exception as e:
                    logger.error(f"Error during recording: {e}")
                    self.in_meeting = False
            else:
                logger.error(f"Could not join meeting {meeting_id}.")

    def monitor_meeting(self, output_path: str) -> None:
        """Poll WeMeet window for active status."""
        logger.info("Monitoring meeting status...")
        while self.in_meeting:
            if not self.joiner.verify_in_meeting():
                logger.info("Meeting ended or window closed.")
                self.in_meeting = False
                break
            time.sleep(30)
            
        logger.info("Stopping recording and saving...")
        self.recorder.stop(output_path)
        logger.info(f"Recording saved to {output_path}")

if __name__ == "__main__":
    agent = MeetingAgent()
    try:
        agent.run()
    except KeyboardInterrupt:
        logger.info("Agent stopped by user.")
    except Exception as e:
        logger.critical(f"Critical error: {e}")
