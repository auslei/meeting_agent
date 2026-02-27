# WeMeet Automated Meeting Agent | 腾讯会议自动加入与录音助手

[English](#english) | [中文](#chinese)

<a name="english"></a>
## English

Automated process to detect WeMeet meeting invitations in WeChat, join them, and record the audio to MP3 files.

### Features
- **Cross-Platform:** Supports Windows, macOS, and Linux.
- **Resolution Independent:** Uses OCR and URL schemes instead of hardcoded coordinates.
- **Automatic Recording:** Records system audio directly to MP3 using loopback.
- **Robust Error Handling:** Modular architecture with status verification and detailed logging.

### Prerequisites

#### 1. External Tools
- **Tesseract OCR:** Required for reading text from windows.
  - **Windows:** Download installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
  - **macOS:** `brew install tesseract`
  - **Linux:** `sudo apt install tesseract-ocr` (Install `tesseract-ocr-chi-sim` for Chinese support).
- **FFmpeg:** Required for MP3 conversion.
  - **Windows:** [Download FFmpeg](https://ffmpeg.org/download.html) and add to PATH.
  - **macOS:** `brew install ffmpeg`
  - **Linux:** `sudo apt install ffmpeg`

#### 2. Audio Loopback (System Audio Capture)
- **Windows:** Uses WASAPI loopback (built-in). No extra driver needed.
- **macOS:** Requires a virtual audio driver like **BlackHole 2ch**. [Download here](https://github.com/ExistentialAudio/BlackHole). Set system output to "BlackHole 2ch" during meetings.
- **Linux:** Uses PulseAudio/PipeWire monitor sinks (built-in). The script handles switching automatically.

### Setup & Running
1. **Install dependencies:**
   ```bash
   uv sync
   ```
2. **Test your environment:**
   ```bash
   PYTHONPATH=. uv run python src/tests/test_env.py
   PYTHONPATH=. uv run python src/tests/test_audio.py
   ```
3. **Run the agent:**
   ```bash
   PYTHONPATH=. uv run python main.py
   ```

---

<a name="chinese"></a>
## 中文

该项目实现了一个自动化流程：监测微信中的腾讯会议邀请，自动加入会议，并将会议音频实时录制为 MP3 文件。

### 功能特性
- **跨平台支持:** 支持 Windows, macOS 和 Linux。
- **分辨率无关:** 使用 OCR 文字识别和 URL Scheme，而非硬编码的坐标，适配各种显示分辨率。
- **自动录音:** 使用回环（Loopback）技术直接将系统声音录制为 MP3。
- **稳定可靠:** 模块化架构，具备状态校验和详细的日志记录。

### 前置条件

#### 1. 外部工具
- **Tesseract OCR:** 用于识别窗口中的文字。
  - **Windows:** 从 [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) 下载安装程序。
  - **macOS:** 执行 `brew install tesseract`。
  - **Linux:** 执行 `sudo apt install tesseract-ocr` (建议安装 `tesseract-ocr-chi-sim` 以支持中文)。
- **FFmpeg:** 用于 MP3 格式转换。
  - **Windows:** [下载 FFmpeg](https://ffmpeg.org/download.html) 并将其 bin 目录添加到系统环境变量 PATH。
  - **macOS:** 执行 `brew install ffmpeg`。
  - **Linux:** 执行 `sudo apt install ffmpeg`。

#### 2. 音频回环 (系统声音采集)
- **Windows:** 使用内置的 WASAPI Loopback，无需额外驱动。
- **macOS:** 需要安装虚拟音频驱动 **BlackHole 2ch** [下载地址](https://github.com/ExistentialAudio/BlackHole)。会议期间需将系统输出设备设置为 "BlackHole 2ch"。
- **Linux:** 使用内置的 PulseAudio/PipeWire Monitor Sink。脚本会自动处理切换。

### 安装与运行
1. **安装依赖:**
   ```bash
   uv sync
   ```
2. **环境测试:**
   验证窗口识别、OCR 以及录音功能：
   ```bash
   PYTHONPATH=. uv run python src/tests/test_env.py
   PYTHONPATH=. uv run python src/tests/test_audio.py
   ```
3. **启动助手:**
   ```bash
   PYTHONPATH=. uv run python main.py
   ```

### 故障排除
- **找不到微信窗口:** 请确保微信窗口处于打开状态且未被最小化。
- **OCR 识别率:** 如果微信界面是中文，请确保 Tesseract 已安装 `chi_sim` 语言包。
- **录音无声音:** 
  - Windows: 检查是否禁用了立体声混音（虽然 WASAPI 通常不需要）。
  - macOS: 检查声音输出是否已手动切换到 BlackHole。
  - Linux: 运行 `pactl list short sources` 确认存在 monitor 设备。
