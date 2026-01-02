# terminal-chat

A terminal-based, OpenAI-compatible chat client for **streaming AI interaction**, automation, and long-form text workflows.

`terminal-chat` supports streaming output, multiple rendering styles, stdin piping, raw automation mode, and an interactive REPL with **safe multiline input**.

---

## Features

- Streaming responses (default) with optional non-streaming mode
- Interactive REPL with persistent, crash-safe conversation history
- **Multiline input support**
  - Explicit mode: `/multiline` → `/end` to submit, `/cancel` to abort
  - Automatic detection for pasted or newline input
- Multiple output styles via `--style`:
  - `rich` (default): ANSI-enhanced Markdown
  - `plain`: Plain text (script-friendly)
  - `clean`: Markdown noise removed (reading/copy-friendly)
- Automatic Markdown table rendering with width limits
- Raw output mode for automation and piping
- stdin (pipe) support as contextual input
- Runtime configuration via `/cmd`
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

Set environment variables:

```bash
export TERMINAL_CHAT_ENDPOINT="https://YOUR_API_ENDPOINT/v1/chat/completions"
export TERMINAL_CHAT_KEY="YOUR_API_KEY"
export TERMINAL_CHAT_MODEL="default-model-name"
```

All values can be overridden via CLI flags or `/cmd`.

---

## Usage

### One-shot prompt

```bash
terminal-chat -p "Explain artificial intelligence in simple terms"
```

### Interactive mode

```bash
terminal-chat --interactive
```

### Multiline input (interactive)

```text
/multiline
<paste or type multiple lines>
/end
```

Abort safely with `/cancel`.

### stdin / pipe mode

```bash
ls -l | terminal-chat -p "Which files look suspicious?"
```

---

## Common Options

```text
-p, --prompt           One-shot prompt
-i, --interactive      Interactive mode
-m, --model            Override model
--max-tokens           Max tokens
--temperature          Sampling temperature
--top-p                Top-p sampling
--style                rich | plain | clean
--raw                  Raw output (CLI only)
--no-stream            Disable streaming
```

---

## Interactive Commands

Available inside interactive mode:

```text
/cmd temperature <float>
/cmd top_p <float>
/cmd max_tokens <int>
/cmd history <int>
/cmd system_prompt <text>
/cmd model <model_name>
/cmd show
/cmd help
```

---

## Notes

- Conversation storage and context window are handled separately
- History is saved after every completed response
- Designed for long prompts, drafting, contracts, and document review
