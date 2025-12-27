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

export CHAT_CLI_ENDPOINT="https://YOUR_API_ENDPOINT/v1/chat/completions"
export CHAT_CLI_KEY="YOUR_API_KEY"

These variables must be set before running the CLI.

---

## Usage

Common usage
```bash
terminal-chat.py <args>
```
Argument options:
```bash
  -h, --help            show this help message and exit
  -p PROMPT, --prompt PROMPT
                        One-shot prompt (CLI mode)
  -i, --interactive     Interactive chat mode
  -m MODEL, --model MODEL
                        Model name
  --max-tokens MAX_TOKENS
                        Max tokens
  --temperature TEMPERATURE
                        Sampling temperature
  --top-p TOP_P         Top-p sampling
  --system-prompt SYSTEM_PROMPT
                        System prompt
  --history HISTORY     History pairs (interactive)
  -r, --raw             Raw output (CLI only)
  --no-stream           Disable streaming (CLI only)
```

---

### Examples

#### Basic usage (streaming mode)
```bash
./terminal-chat.py -p "Explain artificial intelligence in simple terms"
```
#### Specify model
```bash
./terminal-chat.py -p "Explain the rule of law" -m tugasi-chat
```
#### Non-streaming mode

Wait for the full response before rendering (useful for clean tables):
```bash
./terminal-chat.py -p "Explain fintech regulation in Indonesia" --no-stream
```

#### Raw Output Mode (Automation-Friendly)

Raw mode disables all terminal formatting and is intended for scripting and pipelines.

##### Non-streaming raw output
```bash
./terminal-chat.py -p "Summarize contract law in 5 points" --raw --no-stream
```
##### Streaming raw output
```bash
./terminal-chat.py -p "Explain AI alignment" --raw
```
---

## System Prompt

Control model behavior:
```bash
./terminal-chat.py \
  -p "Analyze legal risk of a startup" \
  --system-prompt "You are a legal analyst. Answer concisely and structurally."
```
---

## Sampling Parameters
```bash
./terminal-chat.py \
  -p "Generate a policy outline" \
  --temperature 0.2 \
  --top-p 0.9
```

---

## Interactive Mode (REPL)

### Start interactive mode:
```bash
./terminal-chat.py --interactive
```
### Basic Interaction
- Type prompts after >
- Responses are streamed and rendered automatically
- Conversation history is preserved
- Use /bye to exit the session

---

## Interactive Commands (/cmd)

Inside interactive mode, runtime parameters can be modified without restarting.

Available Commands
```bash
/cmd temperature <float>
/cmd top_p <float>
/cmd max_tokens <int>
/cmd history <int>
/cmd system_prompt <text>
/cmd show
/cmd help
```
### Examples

Change temperature during session:
```bash
/cmd temperature 0.3
```
Update system prompt dynamically:
```bash
/cmd system_prompt You are a senior legal consultant. Answer formally.
```
Adjust conversation history depth:
```bash
/cmd history 20
```
Inspect current session configuration:
```bash
/cmd show
```
Notes
- /cmd is only available in interactive mode
- Changes apply to all subsequent prompts in the same session
- CLI modes (--raw, --no-stream) are unaffected

---

## Command-Line Help

Run without arguments to display full help:
```bash
./terminal-chat.py
```
