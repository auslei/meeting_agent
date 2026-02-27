import time
import os
from src.common.audio_recorder import AudioRecorder
from src.common.logger import agent_logger as logger

def test_recording():
    output_file = "test_system_audio.mp3"
    duration = 10 # seconds
    
    logger.info("Initializing AudioRecorder...")
    recorder = AudioRecorder()
    
    if recorder.device_id is None:
        logger.error("No loopback device found. Please check your system audio settings.")
        return

    logger.info(f"Starting recording for {duration} seconds... Please ensure audio is playing.")
    try:
        recorder.start()
        
        # Countdown
        for i in range(duration, 0, -1):
            logger.info(f"Recording... {i}s remaining")
            time.sleep(1)
        
        logger.info("Stopping recording and saving file...")
        recorder.stop(output_file)
        
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            logger.info(f"SUCCESS: Recording saved to {output_file} ({size} bytes)")
        else:
            logger.error("FAILED: Output file was not created.")
            
    except Exception as e:
        logger.error(f"An error occurred during recording test: {e}")

if __name__ == "__main__":
    test_recording()
