# terminal-chat

An OpenAI-compatible command-line chat client with streaming, rich terminal rendering, and interactive mode support.

---

## Features

- Streaming response output
- Optional non-streaming mode
- Markdown-aware terminal rendering (bold, italic, numbering)
- Automatic table detection and rendering (PrettyTable)
- Adaptive table width based on terminal size
- Numeric column right-alignment in tables
- Interactive (REPL) mode with conversation history
- Runtime parameter control in interactive mode (`/cmd`)
- Compatible with OpenAI-style Chat Completion API

---

## Requirements

- Python 3.8+
- httpx
- prettytable

---

## Installation

```bash
pip install httpx prettytable
git clone https://github.com/koesn/terminal-chat.git
cd terminal-chat
chmod +x terminal-chat.py
```

---

Configuration

Edit the script and set your API endpoint and API key:

URL = "https://YOUR_API_ENDPOINT/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}


---

Usage

Streaming mode (default)
```bash
./terminal-chat.py -p "Explain artificial intelligence in simple terms"
```
Specify model
```bash
./terminal-chat.py -p "Explain the rule of law" -m tugasi-chat
```
Non-streaming mode
```bash
./terminal-chat.py -p "Explain fintech regulation in Indonesia" --no-stream
```
Interactive mode
```bash
./terminal-chat.py --interactive
```
Inside interactive mode:
	•	Type prompts directly after >
	•	Use /cmd help to see available runtime commands
	•	Use /bye to exit

