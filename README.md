# 🎬 Telegram Video Editor Bot

A powerful and user-friendly Telegram bot for quick video editing operations to really level up your shitposting capabilities. Built with Python and powered by FFmpeg.

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- 🔄 **Speed Modification**: Speed up or slow down videos
- ✂️ **Video Cropping**: Trim videos with precise timecodes
- 🔗 **Video Concatenation**: Merge multiple videos into one
- 📊 **Queue System**: Efficient handling of multiple requests
- 🔄 **Real-time Updates**: Live queue position updates

## 🚀 Getting Started

### Prerequisites

- Python 3.13 
- Poetry
- FFmpeg installed on your system

### Installation

1. Clone the repository:
```bash
git clone https://github.com/fobbidennotis/telegram-editor-bot
cd telegram-editor-bot
```

2. Install the required dependencies:
```bash
poetry lock
poetry install
```

3. Set up your environment variables:
```bash
export TG_BOT_TOKEN="your_telegram_bot_token"
```

4. Create necessary directories:
```bash
mkdir -p vids/input vids/output
```

5. Run the bot:
```bash
poetry run python3 main.py
```

## 🎯 Usage

1. Start a chat with the bot on Telegram
2. Send a video file
3. Choose one of the available operations:
   - **Crop**: Trim video using timecodes (format: HH:MM:SS)
   - **Modify speed**: Change video playback speed
   - **Concat**: Merge multiple videos together

## 🏗️ Project Structure

```
telegram-editor-bot/
├── main.py           # Main bot logic and handlers
├── task_queue.py     # Queue management system
├── videoedit.py      # Video processing functions
├── vids/
│   ├── input/       # Temporary storage for input videos
│   └── output/      # Temporary storage for processed videos
```

## 🛠️ Technical Details

- Uses `aiogram` for Telegram bot functionality
- Implements `moviepy` and `FFmpeg` for video processing
- Features a robust queue system for handling multiple requests
- Supports various time formats for video cropping
- Automatically normalizes videos for concatenation

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Fork the repository and send a PR with your changes. Feel free to check the issues page.
