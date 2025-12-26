# terminal-chat

A minimal OpenAI-compatible command-line chat client with streaming support.

---

## Features

- Simple command-line interface
- Streaming response output
- Compatible with OpenAI-style Chat Completion API
- Configurable model selection
- Optional non-streaming mode

---

## Requirements

- Python 3.8+
- httpx

---

## Installation

```bash
pip install httpx
git clone https://github.com/koesn/terminal-chat.git
cd terminal-chat
chmod +x terminal-chat.py
```

---

## Configuration

Edit the script and set your API endpoint and API key:

URL = "https://YOUR_API_ENDPOINT/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}


---

## Usage

Streaming mode (default):
```bash
./terminal-chat.py -p "Explain artificial intelligence in simple terms"
```
Specify model:

```bash
./terminal-chat.py -p "Explain the rule of law" -m tugasi-chat
```
Non-streaming mode:

```bash
./terminal-chat.py -p "Explain fintech regulation in Indonesia" --no-stream
```
