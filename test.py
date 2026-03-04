from pywinauto import Application
import os
import time

def join_meeting(meeting_id):  
    os.startfile("C:\\Program Files\\Tencent\\WeMeet\\WeMeetApp.exe")
    time.sleep(2)
    app = Application(backend="uia").connect(title_re=r".*(Tencent Meeting|腾讯会议).*")

    if app:
        print("WeMeet is running")
    else:
        print("WeMeet is not running")
        exit(1)

    wm_window = app.window(title="腾讯会议")

    wm_window.set_focus()
    print("focused..")
    time.sleep(1)

    rect = wm_window.rectangle()

    click_x = rect.left + 310 
    click_y = rect.top + 401

    # 3. Perform the click at the dynamic location
    import pywinauto
    pywinauto.mouse.click(coords=(click_x, click_y))
    print(f"clicked on {click_x}, {click_y}")
    
    join_window = app.window(title="加入会议")
    join_window.set_focus()

    time.sleep(1)
    join_window.type_keys(meeting_id)
    join_window.type_keys("{ENTER}")


def recording(duration: int, file_path: str, auto_silence_stop: int):
    """
    Start recording the meeting using ffmpeg, the goal is to record all audio using computer input. It should also work 
    on servers and virtual machines.

    - if duration is -1, it will record until auto_silence_stop is reached.
    - if duration is not -1, it will record for the specified duration or until auto_silence_stop is reached.
    - if auto_silence_stop is -1, it will be ignored.
    
    duration: duration of recording in seconds
    file_path: path to save the recording
    auto_silence_stop: auto silence stop in seconds
    """
    
import subprocess
import time
import os
import wave
import numpy as np
import pyaudio

def get_audio_device():
    """Detects the OS and returns the appropriate FFmpeg device string."""
    import platform
    current_os = platform.system()
    
    if current_os == "Windows":
        # Uses DirectShow to find audio devices
        return "audio=Microphone"  # You may need to verify exact name via: ffmpeg -list_devices true -f dshow -i dummy
    elif current_os == "Linux":
        return "default" # PulseAudio/ALSA default
    else:
        return ":0" # macOS/Darwin


ffmpeg_path = "C:\\Users\\ausle\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.0.1-full_build\\bin\\ffmpeg.exe"

def recording(duration: int, file_path: str, auto_silence_stop: int):
    # Constants for silence detection
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    SILENCE_THRESHOLD = 500  # Adjust based on background noise
    
    device_name = get_audio_device()
    f_backend = "dshow" if os.name == "nt" else "pulse"
    
    # Start FFmpeg process
    ffmpeg_cmd = [
        ffmpeg_path, '-y', '-f', f_backend, '-i', device_name,
        '-acodec', 'libmp3lame', file_path
    ]
    
    process = subprocess.Popen(ffmpeg_cmd)
    
    # Initialize PyAudio for silence monitoring
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    start_time = time.time()
    silence_duration = 0
    
    try:
        print(f"Recording started to {file_path}...")
        while True:
            elapsed = time.time() - start_time
            
            # Check for duration limit
            if duration != -1 and elapsed >= duration:
                print("Duration limit reached.")
                break
            
            # Check for silence
            if auto_silence_stop != -1:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                peak = np.max(np.abs(audio_data))
                
                if peak < SILENCE_THRESHOLD:
                    silence_duration += (CHUNK / RATE)
                else:
                    silence_duration = 0
                
                if silence_duration >= auto_silence_stop:
                    print(f"Auto-stop: {auto_silence_stop}s of silence detected.")
                    break
            
            time.sleep(0.1)
            
    finally:
        # Graceful shutdown
        process.terminate()
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Recording saved.")

#join_meeting("979260822")
recording(duration=10, file_path="c:/mp3s/test.mp3", auto_silence_stop=5)

#join_meeting("721303291")
# join_btn = wm_window.child_window(title = "加入会议", top_level_only=False)
# join_btn.wait('ready', timeout=10)
# join_btn.click_input()

#join_btn = wm_window.child_window(title_re=r".*(加入会议|Join).*", control_type ="Button")
#join_btn.click_input()

# Chains down the 'Custom' layers seen in your Inspector screenshot
# window -> DialogWidget -> MainWidget -> NXViewRoot -> custom(0) -> custom(0) -> button
# target = wm_window.DialogWidget.MainWidget.NXViewRoot.\
#     child_window(control_type="Custom", found_index=0)\
#     .child_window(control_type="Custom", found_index=0)\
#     .child_window(title="加入会议")

# target.click_input()
