import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from src.common.logger import agent_logger as logger
import platform
import os
import threading
import time
import subprocess
from typing import List, Optional

class AudioRecorder:
    """
    Cross-platform system audio recorder using loopback.
    """
    def __init__(self, sample_rate: int = 44100, channels: int = 2):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.data: List[np.ndarray] = []
        self._thread: Optional[threading.Thread] = None
        self.device_id = self._get_loopback_device()
        self._original_default_source = None

    def _get_loopback_device(self) -> Optional[int]:
        """Find the system audio loopback device ID (Windows WASAPI only)."""
        devices = sd.query_devices()
        
        for i, dev in enumerate(devices):
            try:
                hostapi_info = sd.query_hostapis(dev["hostapi"])
                api_name = hostapi_info["name"]
            except Exception:
                api_name = ""
                
            if "WASAPI" in api_name and dev["max_input_channels"] > 0:
                if "loopback" in dev["name"].lower():
                    logger.info(f"Found Windows loopback device: {dev['name']} (ID: {i})")
                    return i
                    
        logger.warning("No WASAPI loopback device found.")
        return sd.default.device[0]

    def _record_callback(self, indata, frames, time, status):
        """Callback for sounddevice stream."""
        if status:
            logger.error(f"Recording status error: {status}")
        if self.recording:
            self.data.append(indata.copy())
            # Calculate current RMS volume
            self.current_volume = np.sqrt(np.mean(indata**2))

    def is_silent(self, threshold: float = 0.005) -> bool:
        """Check if the current audio level is below a threshold."""
        if not hasattr(self, 'current_volume'):
            return True
        return self.current_volume < threshold

    def start(self) -> None:
        """Start recording in a background thread."""
        if self.recording:
            logger.warning("Already recording.")
            return

        self.recording = True
        self.data = []
        self.current_volume = 0.0
        
        def run():
            try:
                with sd.InputStream(device=self.device_id,
                                     channels=self.channels,
                                     samplerate=self.sample_rate,
                                     callback=self._record_callback):
                    while self.recording:
                        sd.sleep(100)
            except Exception as e:
                logger.error(f"Error in recording stream: {e}")
                self.recording = False

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        logger.info("Started recording audio.")

    def stop(self, output_path: str = "meeting_record.mp3") -> None:
        """Stop recording and save to MP3."""
        if not self.recording:
            logger.warning("No recording in progress.")
            return

        self.recording = False
        if self._thread:
            self._thread.join()

        if not self.data:
            logger.error("No audio data recorded.")
            return

        logger.info(f"Processing audio data and saving to {output_path}...")
        
        try:
            audio_array = np.concatenate(self.data, axis=0)
            audio_int16 = (audio_array * 32767).astype(np.int16)
            
            audio_segment = AudioSegment(
                audio_int16.tobytes(),
                frame_rate=self.sample_rate,
                sample_width=2,
                channels=self.channels
            )
            
            audio_segment.export(output_path, format="mp3")
            logger.info(f"Successfully saved recording to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
