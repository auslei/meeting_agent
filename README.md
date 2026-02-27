# WeMeet Automated Meeting Agent

An automated process to detect WeMeet meeting invitations in WeChat, join them, and record the audio to MP3 files.

## Features
- **Cross-Platform:** Supports Windows, macOS, and Linux.
- **Resolution Independent:** Uses OCR and URL schemes instead of hardcoded coordinates.
- **Automatic Recording:** Records system audio directly to MP3 using loopback.
- **Robust Error Handling:** Modular architecture with status verification and detailed logging.

## Prerequisites

### 1. External Tools
- **Tesseract OCR:** Required for reading text from windows.
  - Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`
  - macOS: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`
- **FFmpeg:** Required for `pydub` to export MP3 files.
  - Windows: [Download FFmpeg](https://ffmpeg.org/download.html) and add to PATH.
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### 2. Audio Loopback (System Audio Capture)
- **Windows:** Uses WASAPI loopback (built-in).
- **macOS:** Requires a virtual audio driver like **BlackHole 2ch**. [Download here](https://github.com/ExistentialAudio/BlackHole).
- **Linux:** Uses PulseAudio/PipeWire monitor sinks (built-in).

## Project Structure
- `main.py`: Main entry point to orchestrate the agent.
- `src/common/`: Shared tools (Logger, GUI Interactor, Audio Recorder).
- `src/wechat/`: WeChat monitoring logic.
- `src/wemeet/`: WeMeet join and verification logic.
- `src/tests/`: Diagnostic and validation scripts.

## Setup & Testing
Ensure you have `uv` installed.

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Test your environment:**
   Verify that WeChat and WeMeet are detected and OCR is working.
   ```bash
   PYTHONPATH=. uv run python src/tests/test_env.py
   ```

3. **Run the agent:**
   ```bash
   PYTHONPATH=. uv run python main.py
   ```

## How it Works
1. **Watch:** The agent polls the WeChat window for meeting IDs or `meeting.tencent.com` links using OCR.
2. **Join:** It attempts to join via the `wemeet://` URL scheme. If that fails, it uses the GUI.
3. **Verify:** It verifies the join by looking for meeting controls (e.g., "Mute" button).
4. **Record:** It starts recording system audio to a temporary buffer and exports to `recordings/` as an MP3 file when the meeting ends.

## Troubleshooting
- **WeChat not found:** Ensure the WeChat window is open and visible (not minimized).
- **OCR accuracy:** Ensure you have the `chi_sim` (Chinese Simplified) language pack installed for Tesseract if your WeChat is in Chinese.
- **Audio failed:** Ensure the correct loopback device is selected. On macOS, set your system output to "BlackHole 2ch".
