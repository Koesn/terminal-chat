# terminal-chat

A terminal-based, OpenAI-compatible chat client designed for both human-friendly interaction and automation workflows.

`terminal-chat` supports streaming responses, multiple rendering styles, stdin piping as context, raw output for automation, and an interactive REPL with proper line-editing support.

---

## Features

* Streaming response output (default)
* Optional non-streaming mode
* Raw output mode for automation and piping
* Multiple output styles via `--style`:

  * `rich`  — ANSI-enhanced Markdown rendering (default)
  * `plain` — Plain text output without ANSI styling
  * `clean` — Human-readable prose with Markdown noise removed
* Markdown-aware terminal rendering (bold, italic, headings)
* Automatic Markdown table detection and rendering (PrettyTable)
* Defensive handling of malformed tables from LLM output
* Adaptive table width with hard column caps for readability
* Numeric column right-alignment in tables
* Interactive (REPL) mode with persistent conversation history
* Crash-safe conversation storage (saved after every response)
* Runtime configuration via `/cmd` inside interactive mode
* Proper terminal line-editing support (arrow keys, word navigation)
* stdin (pipe) support as contextual input
* Safe stdin truncation to prevent excessive prompt size
* System prompt support
* Compatible with OpenAI-style Chat Completion API

---

## Requirements

* Python 3.8+
* httpx
* prettytable

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

`terminal-chat` reads configuration from environment variables.

```bash
export TERMINAL_CHAT_ENDPOINT="https://YOUR_API_ENDPOINT/v1/chat/completions"
export TERMINAL_CHAT_KEY="YOUR_API_KEY"
export TERMINAL_CHAT_MODEL="default-model-name"
```

* `TERMINAL_CHAT_MODEL` acts as the default model
* All values can be overridden at runtime via CLI flags or `/cmd`

---

## Usage

### Common usage

```bash
terminal-chat <args>
```

### Argument options

```bash
-h, --help              show this help message and exit
-p PROMPT, --prompt PROMPT
                        One-shot prompt (CLI mode)
-i, --interactive       Interactive chat mode
-m MODEL, --model MODEL
                        Model name (override TERMINAL_CHAT_MODEL)
--max-tokens MAX_TOKENS
                        Max tokens
--temperature TEMPERATURE
                        Sampling temperature
--top-p TOP_P           Top-p sampling
--system-prompt SYSTEM_PROMPT
                        System prompt
--history HISTORY       Context history pairs (interactive)
--style {rich,plain,clean}
                        Output rendering style
-r, --raw               Raw output (CLI only)
--no-stream             Disable streaming (CLI only)
```

---

## Examples

### Basic usage (streaming mode)

```bash
terminal-chat -p "Explain artificial intelligence in simple terms"
```

### Specify model

```bash
terminal-chat -p "Explain the rule of law" -m tugasi-chat
```

### Non-streaming mode

Wait for the full response before rendering (useful for clean tables):

```bash
terminal-chat -p "Explain fintech regulation in Indonesia" --no-stream
```

---

## Output Styles

### Rich (default)

ANSI-enhanced Markdown rendering with bold, italic, headings, and tables.

```bash
terminal-chat -p "Explain constitutional law"
```

### Plain

Plain text output without ANSI styling. Suitable for piping and scripting.

```bash
terminal-chat -p "Explain constitutional law" --style plain
```

### Clean

Human-readable prose mode. Removes Markdown noise such as:

* `**bold**`, `*italic*`
* Blockquotes (`>`)
* Heading markers (`#`)
* Horizontal rules (`---`)

Optimized for long reading and copy–paste.

```bash
terminal-chat -p "Explain constitutional law" --style clean
```

---

## stdin / Pipe Mode

`terminal-chat` can accept stdin as contextual input.

### Pipe without prompt

```bash
ls -l | terminal-chat
```

### Pipe with prompt

```bash
ls -l | terminal-chat -p "Which files look suspicious?"
```

stdin is injected as context, followed by the user prompt.

---

## Raw Output Mode (Automation-Friendly)

Raw mode disables all rendering and formatting.

### Non-streaming raw output

```bash
terminal-chat -p "Summarize contract law in 5 points" --raw --no-stream
```

### Streaming raw output

```bash
terminal-chat -p "Explain AI alignment" --raw
```

---

## System Prompt

```bash
terminal-chat \
  -p "Analyze legal risk of a startup" \
  --system-prompt "You are a legal analyst. Answer concisely and structurally."
```

---

## Interactive Mode (REPL)

### Start interactive mode

```bash
terminal-chat --interactive
```

### Behavior

* Proper line editing (arrow keys, word navigation)
* History navigation with ↑ / ↓
* Cursor movement with ← / →
* Responses are streamed and rendered automatically
* Conversation history is restored on startup
* Use `/bye` to exit the session

---

## Interactive Commands (/cmd)

Available commands:

```bash
/cmd temperature <float>
/cmd top_p <float>
/cmd max_tokens <int>
/cmd history <int>
/cmd system_prompt <text>
/cmd model <model_name>
/cmd show
/cmd help
```

Notes:

* `/cmd` is only available in interactive mode
* Changes apply to subsequent prompts only
* Storage history and context window are handled separately

---

## Command-Line Help

Run without arguments to display help and environment status:

```bash
terminal-chat
```
