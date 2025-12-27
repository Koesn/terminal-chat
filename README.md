# terminal-chat

A terminal-based, OpenAI-compatible chat client designed for both human-friendly interaction and automation workflows.

`terminal-chat` supports streaming responses, rich terminal rendering (Markdown and tables), raw output for pipelines, and an interactive REPL mode.

---

## Features

- Streaming response output (default)
- Optional non-streaming mode
- Raw output mode for automation and piping
- Markdown-aware terminal rendering (bold, italic, numbering)
- Automatic Markdown table detection and rendering (PrettyTable)
- Adaptive table width based on terminal size
- Numeric column right-alignment in tables
- Interactive (REPL) mode with conversation history
- Configurable conversation history depth
- System prompt support
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

## Configuration

terminal-chat reads configuration from environment variables.

Set the API endpoint and API key:
```bash
export CHAT_CLI_ENDPOINT="https://YOUR_API_ENDPOINT/v1/chat/completions"
export CHAT_CLI_KEY="YOUR_API_KEY"
```
These variables must be set before running the CLI.

---

## Usage

### Basic usage (streaming mode)
```bash
./terminal-chat.py -p "Explain artificial intelligence in simple terms"
```
### Specify model
```bash
./terminal-chat.py -p "Explain the rule of law" -m tugasi-chat
```
### Non-streaming mode
Wait for the full response before rendering (useful for clean tables):
```bash
./terminal-chat.py -p "Explain fintech regulation in Indonesia" --no-stream
```
### Raw output mode (automation-friendly)

Disable all terminal formatting.

### Non-streaming raw output:
```bash
./terminal-chat.py -p "Summarize contract law in 5 points" --raw --no-stream
```
### Streaming raw output:
```bash
./terminal-chat.py -p "Explain AI alignment" --raw
```
### System prompt

Control model behavior:
```bash
./terminal-chat.py \
  -p "Analyze legal risk of a startup" \
  --system-prompt "You are a legal analyst. Answer concisely and structurally."
```
### Sampling parameters
```bash
./terminal-chat.py \
  -p "Generate a policy outline" \
  --temperature 0.2 \
  --top-p 0.9
```
### Interactive mode
```bash
./terminal-chat.py --interactive
```
In interactive mode:
- Type prompts after >
- Conversation history is preserved automatically
- Use /bye to exit
### Command-Line Help

Run without arguments to see full help:
```bash
./terminal-chat.py
```
