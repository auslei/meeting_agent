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
        """Find the system audio loopback device ID."""
        devices = sd.query_devices()
        system = platform.system()
        
        logger.info(f"System: {system}")
        
        if system == "Windows":
            for i, dev in enumerate(devices):
                if "WASAPI" in dev["hostapi_name"] and dev["max_input_channels"] > 0:
                    if "loopback" in dev["name"].lower():
                        logger.info(f"Found Windows loopback device: {dev['name']} (ID: {i})")
                        return i
            logger.warning("No WASAPI loopback device found.")
            
        elif system == "Linux":
            # On Linux, we try to find the monitor sink using pactl
            try:
                # Get the default sink
                sink_cmd = "pactl info | grep 'Default Sink' | cut -d' ' -f3"
                default_sink = subprocess.check_output(sink_cmd, shell=True).decode().strip()
                monitor_source = f"{default_sink}.monitor"
                
                logger.info(f"Detected default sink: {default_sink}")
                logger.info(f"Targeting monitor source: {monitor_source}")
                
                # We will set this as the default source temporarily when starting
                self._target_monitor_source = monitor_source
                
                # Find the 'pulse' or 'default' device index in sounddevice
                for i, dev in enumerate(devices):
                    if dev['name'] in ['pulse', 'default'] and dev['max_input_channels'] > 0:
                        logger.info(f"Using Linux {dev['name']} device (ID: {i}) with PulseAudio routing.")
                        return i
            except Exception as e:
                logger.error(f"Failed to detect PulseAudio monitor: {e}")
            
        elif system == "Darwin": # macOS
            for i, dev in enumerate(devices):
                if "BlackHole" in dev["name"]:
                    logger.info(f"Found macOS BlackHole device: {dev['name']} (ID: {i})")
                    return i
            logger.error("macOS requires BlackHole for loopback recording.")
            
        return sd.default.device[0]

    def _prepare_linux_recording(self):
        """On Linux, set the default source to the monitor sink."""
        if platform.system() == "Linux" and hasattr(self, '_target_monitor_source'):
            try:
                # Save current default source
                curr_cmd = "pactl info | grep 'Default Source' | cut -d' ' -f3"
                self._original_default_source = subprocess.check_output(curr_cmd, shell=True).decode().strip()
                
                # Set default source to monitor
                logger.info(f"Setting default source to {self._target_monitor_source}")
                subprocess.run(["pactl", "set-default-source", self._target_monitor_source], check=True)
            except Exception as e:
                logger.error(f"Failed to prepare Linux recording: {e}")

    def _cleanup_linux_recording(self):
        """On Linux, restore the original default source."""
        if platform.system() == "Linux" and self._original_default_source:
            try:
                logger.info(f"Restoring default source to {self._original_default_source}")
                subprocess.run(["pactl", "set-default-source", self._original_default_source], check=True)
            except Exception as e:
                logger.error(f"Failed to cleanup Linux recording: {e}")

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

        self._prepare_linux_recording()
        
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
            
        self._cleanup_linux_recording()

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
