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

    def run(self) -> None:
        logger.info("Starting Meeting Agent...")
        
        for event in self.watcher.watch(POLL_INTERVAL):
            if self.in_meeting:
                logger.info(f"Already in a meeting. Ignoring: {event}")
                continue

            meeting_id = event["value"]
            logger.info(f"Detected meeting info: {meeting_id}. Attempting to join...")
            
            success = self.joiner.join_via_scheme(meeting_id)
            if not success:
                logger.warning(f"Failed via scheme. Trying GUI fallback...")
                success = self.joiner.join_via_gui(meeting_id)
            
            if success:
                self.in_meeting = True
                logger.info("Successfully joined meeting. Starting recording...")
                
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
