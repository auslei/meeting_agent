import time
import os
import threading
from src.common.logger import agent_logger as logger
from src.common.gui_interactor import GUIInteractor
from src.wemeet.joiner import WeMeetJoiner
from src.common.audio_recorder import AudioRecorder

# Configuration
RECORDINGS_DIR = "recordings"

os.makedirs(RECORDINGS_DIR, exist_ok=True)

class MeetingAgent:
    """
    Main agent that orchestrates WeMeet joining and audio recording.
    Now triggered via API rather than monitoring WeChat.
    """
    def __init__(self):
        self.interactor = GUIInteractor()
        self.joiner = WeMeetJoiner(self.interactor)
        self.recorder = AudioRecorder()
        self.in_meeting = False
        
        # In-memory store to track recording state: { meeting_id: {"status": str, "file": str} }
        self.state_registry = {}
        self._lock = threading.Lock()

    def get_meeting_state(self, meeting_id: str) -> dict:
        """Return the state dict for a given meeting ID."""
        with self._lock:
            return self.state_registry.get(meeting_id, {"status": "not_found", "file": None})

    def _set_meeting_state(self, meeting_id: str, status: str, file_path: str = None):
        """Update the state for a given meeting."""
        with self._lock:
            if meeting_id not in self.state_registry:
                self.state_registry[meeting_id] = {}
            self.state_registry[meeting_id]["status"] = status
            if file_path is not None:
                self.state_registry[meeting_id]["file"] = file_path

    def process_meeting(self, meeting_id: str) -> None:
        """
        Attempt to join, monitor, and record the specified meeting.
        Should be run as a background task.
        """
        logger.info(f"Agent instructed to process meeting: {meeting_id}")
        
        with self._lock:
            if self.in_meeting:
                logger.warning(f"Already in a meeting. Cannot process: {meeting_id}")
                self._set_meeting_state(meeting_id, "failed - already in meeting")
                return
            self.in_meeting = True
            
        self._set_meeting_state(meeting_id, "joining")

        logger.info(f"Attempting to join meeting {meeting_id} via GUI automation...")
        
        success = self.joiner.join_via_gui(meeting_id)
        if not success:
            logger.warning(f"Failed via GUI. Trying scheme fallback...")
            success = self.joiner.join_via_scheme(meeting_id)
        
        if success:
            self._set_meeting_state(meeting_id, "in_progress")
            logger.info(f"Successfully joined meeting {meeting_id}. Starting recording...")
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(RECORDINGS_DIR, f"meeting_{meeting_id}_{timestamp}.mp3")
            
            try:
                self.recorder.start()
                self.monitor_meeting(meeting_id, output_path)
            except Exception as e:
                logger.error(f"Error during recording: {e}")
                self._set_meeting_state(meeting_id, "failed", output_path)
                with self._lock:
                    self.in_meeting = False
        else:
            logger.error(f"Could not join meeting {meeting_id}.")
            self._set_meeting_state(meeting_id, "failed")
            with self._lock:
                self.in_meeting = False

    def monitor_meeting(self, meeting_id: str, output_path: str) -> None:
        """Poll WeMeet window and check for silence to determine meeting end."""
        logger.info("Monitoring meeting status...")
        silence_start = None
        silence_threshold_mins = 5
        
        while self.in_meeting:
            # 1. Check if window is still there
            if not self.joiner.verify_in_meeting():
                logger.info("Meeting window disappeared. Assuming meeting ended.")
                self.in_meeting = False
                break
            
            # 2. Check for silence
            if self.recorder.is_silent():
                if silence_start is None:
                    silence_start = time.time()
                
                silence_duration = (time.time() - silence_start) / 60
                logger.debug(f"Silence detected: {silence_duration:.1f} mins")
                
                if silence_duration >= silence_threshold_mins:
                    logger.info(f"Silence exceeded {silence_threshold_mins} mins. Ending meeting.")
                    self.in_meeting = False
                    self.joiner.close_meeting()
                    break
            else:
                if silence_start is not None:
                    logger.info("Audio resumed. Resetting silence timer.")
                silence_start = None

            time.sleep(30) # Check every 30 seconds
            
        logger.info("Stopping recording and saving...")
        self.recorder.stop(output_path)
        logger.info(f"Recording saved to {output_path}")
        self._set_meeting_state(meeting_id, "completed", output_path)

if __name__ == "__main__":
    logger.info("Main script directly executed. Please run the service using `uv run uvicorn service:app --host 0.0.0.0 --port 8888` instead.")
