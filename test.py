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


ffmpeg_path = "C:\\Users\\ausle\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.0.1-full_build\\bin\\ffmpeg.exe"
import subprocess
import re
import time
import os
import numpy as np
import pyaudio

def get_windows_audio_device():
    """
    Finds the 'Stereo Mix' device to record computer output.
    """
    cmd = [ffmpeg_path, '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy']
    result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    
    # Extract all audio devices
    devices = re.findall(r'"([^"]+)" \(audio\)', result.stderr)
    
    # 1. Target the computer output specifically
    for d in devices:
        if any(term in d for term in ["Stereo Mix", "What U Hear", "Wave Out"]):
            print(f"Success: Found Output Device -> {d}")
            return f"audio={d}"
    
    # 2. If Stereo Mix isn't found, list what IS available so you can troubleshoot
    print("AVAILABLE DEVICES FOUND:")
    for i, d in enumerate(devices):
        print(f" [{i}] {d}")
        
    raise RuntimeError("Stereo Mix not found. Please enable it in Windows Sound Settings.")


def recording(duration: int, file_path: str, auto_silence_stop: int):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    SILENCE_THRESHOLD = 500 

    try:
        device_name = "audio=CABLE Output (VB-Audio Virtual Cable)" #get_windows_audio_device()
        print(f"Attempting to record from: {device_name}")
    except Exception as e:
        print(f"Error: {e}")
        return

    # Using '-t' inside FFmpeg for the duration is more reliable than manually killing it
    ffmpeg_cmd = [
        ffmpeg_path, '-y', 
        '-f', 'dshow', 
        '-i', device_name,
        '-acodec', 'libmp3lame',
        '-t', str(duration) if duration != -1 else '3600', # Default 1 hour if -1
        file_path
    ]
    
    # We remove DEVNULL so you can see the error if it fails to start
    process = subprocess.Popen(ffmpeg_cmd)

    # Silence monitoring logic
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    start_time = time.time()
    silence_count = 0

    try:
        while process.poll() is None: # While FFmpeg is still running
            if auto_silence_stop != -1:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                if np.abs(audio_data).mean() < SILENCE_THRESHOLD:
                    silence_count += (CHUNK / RATE)
                    if silence_count >= auto_silence_stop:
                        print("Silence detected. Stopping...")
                        break
                else:
                    silence_count = 0
            time.sleep(0.1)
    finally:
        process.terminate()
        stream.close()
        p.terminate()
        print(f"Recording closed. Check {file_path} size.")


#join_meeting("979260822")
recording(duration=10, file_path="./test.mp3", auto_silence_stop=5)

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
