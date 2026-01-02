#!/usr/bin/env python3

import readline
readline.parse_and_bind("tab: complete")
import os
import httpx
import json
import argparse
import shutil
import textwrap
import re
import sys
from prettytable import PrettyTable
import atexit

# ======================================================
# CONVERSATION HISTORY
# ======================================================
CONVERSATION_STORE_LIMIT = 1000  # jumlah MESSAGE, bukan pair
CONVERSATION_FILE = os.path.expanduser("~/.terminal-chat-conversation.json")
HISTORY_FILE = os.path.expanduser("~/.terminal-chat-history")

try:
    readline.read_history_file(HISTORY_FILE)
except FileNotFoundError:
    pass
    
atexit.register(readline.write_history_file, HISTORY_FILE)

# ======================================================
# TERMINAL
# ======================================================
class Terminal:
    def __init__(self):
        self.ansi = sys.stdout.isatty()
        
    def disable_ansi(self):
        self.ansi = False

    def width(self):
        return shutil.get_terminal_size((80, 20)).columns

    def color(self, code):
        return code if self.ansi else ""

TERM = Terminal()

ANSI_RESET = TERM.color("\033[0m")
ANSI_BOLD  = TERM.color("\033[1m")
ANSI_WHITE = TERM.color("\033[97m")
ANSI_GRAY  = TERM.color("\033[90m")
MAX_STDIN_CHARS = 10000
STYLE_MODE = "rich"

# ======================================================
# MARKDOWN → ANSI
# ======================================================
class Markdown:
    @staticmethod
    def style(text: str) -> str:
        global STYLE_MODE
        
        # CLEAN MODE: human-readable prose
        if STYLE_MODE == "clean":
            # remove bold / italic markers
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
            text = re.sub(r"\*(.+?)\*", r"\1", text)
            
            # remove blockquote marker '>'
            text = re.sub(r"^\s*>\s?", "", text)
            
            # strip heading hashes but KEEP the text
            text = re.sub(r"^#{1,6}\s+", "", text)
            
            # drop horizontal rules entirely (---, ----, etc)
            if re.match(r"^\s*-{3,}\s*$", text):
                return None
            
            return text.rstrip()
        
        # PLAIN MODE: no ANSI, no transformation
        if not TERM.ansi:
            return text
        
        # RICH MODE (existing behavior)
        text = re.sub(
            r"\*\*(.+?)\*\*",
            lambda m: f"{ANSI_BOLD}{m.group(1)}{ANSI_RESET}",
            text
        )
        
        text = re.sub(
            r"\*(.+?)\*",
            lambda m: f"{ANSI_GRAY}{m.group(1)}{ANSI_RESET}",
            text
        )
        
        text = re.sub(
            r"^(#{1,3})\s+(.*)$",
            lambda m: f"{ANSI_BOLD}{m.group(2)}{ANSI_RESET}",
            text,
            flags=re.MULTILINE
        )
        
        return text

# ======================================================
# RENDERER
# ======================================================
class Renderer:
    @staticmethod
    def prose(line: str):
        styled = Markdown.style(line.rstrip("\n").rstrip())
        if styled is None:
            return
        
        wrapped = textwrap.fill(
            styled,
            width=TERM.width(),
            replace_whitespace=False,
            drop_whitespace=False
        )
        print(wrapped)

    @staticmethod
    def table(markdown_block: str):
        # ======================================================
        # PARSE MARKDOWN TABLE
        # ======================================================
        lines = [l.rstrip() for l in markdown_block.splitlines() if l.strip()]
        headers = [h.strip() for h in lines[0].strip("|").split("|")]
        
        rows = []
        for row in lines[2:]:
            if "|" in row:
                rows.append([c.strip() for c in row.strip("|").split("|")])
                
        col_count = len(headers)
        
        # ======================================================
        # DETECT NUMERIC COLUMNS
        # ======================================================
        def is_numeric_column(idx):
            for r in rows:
                if idx >= len(r):
                    return False
                v = re.sub(r"[,%\s]", "", r[idx])
                if not v.replace(".", "").isdigit():
                    return False
            return True
        
        numeric_cols = {i for i in range(col_count) if is_numeric_column(i)}
        
        # ======================================================
        # NORMALIZE ROWS
        # ======================================================
        normalized_rows = []
        for r in rows:
            if len(r) < col_count:
                r = r + [""] * (col_count - len(r))
            elif len(r) > col_count:
                r = r[:col_count]
            normalized_rows.append(r)
            
        styled_headers = [Markdown.style(h) for h in headers]
        
        # ======================================================
        # PASS 1 — BUILD TABLE WITHOUT WRAPPING
        # ======================================================
        table = PrettyTable(styled_headers)
        
        for i, h in enumerate(styled_headers):
            table.align[h] = "r" if i in numeric_cols else "l"
            
        for r in normalized_rows:
            table.add_row([
                Markdown.style(cell) if cell else ""
                for cell in r
            ])
            
        # Render once to let PrettyTable decide natural widths
        table_str = table.get_string()
        
        # ======================================================
        # EXTRACT COLUMN WIDTHS (STABLE METHOD)
        # ======================================================
        first_border = table_str.splitlines()[0]
        raw_widths = [
            len(seg)
            for seg in first_border.split("+")[1:-1]
        ]
        
        # ======================================================
        # APPLY HARD CAP FOR READABILITY
        # ======================================================
        HARD_MAX_COL_WIDTH = 35  # ← keputusan desain final
        
        col_widths = []
        for idx, header in enumerate(headers):
            header_len = len(header)
            natural = raw_widths[idx]
            
            col_widths.append(
                min(
                    HARD_MAX_COL_WIDTH,
                    max(header_len + 2, natural)
                )
            )
            
        # ======================================================
        # PASS 2 — REBUILD TABLE WITH WRAPPING
        # ======================================================
        table = PrettyTable(styled_headers)
        
        for i, h in enumerate(styled_headers):
            table.align[h] = "r" if i in numeric_cols else "l"
            
        for r in normalized_rows:
            rendered = []
            for idx, cell in enumerate(r):
                styled = Markdown.style(cell)
                
                # normalize HTML <br> into newline
                if styled:
                    styled = re.sub(r"<br\s*/?>", "\n", styled, flags=re.IGNORECASE)
                    
                wrap_width = max(5, col_widths[idx] - 2)  # padding
                
                wrapped = "\n".join(
                    line.rstrip()
                    for line in textwrap.wrap(
                        styled or "",
                        width=wrap_width,
                        break_long_words=False,
                        break_on_hyphens=False,
                        replace_whitespace=False,
                        drop_whitespace=False,
                    )
                )
                
                rendered.append(wrapped)
                
            table.add_row(rendered)
            
        print(table)

# ======================================================
# TABLE STATE MACHINE
# ======================================================
class TableState:
    def __init__(self):
        self.state = "NONE"
        self.lines = []

    def feed(self, line: str):
        stripped = line.strip()

        if self.state == "NONE":
            if "|" in stripped:
                self.state = "HEADER"
                self.lines = [line]
                return "HOLD"
            return "NO"

        if self.state == "HEADER":
            if re.match(r"^\|?\s*-+\s*(\|\s*-+\s*)+\|?$", stripped):
                self.state = "TABLE"
                self.lines.append(line)
                return "HOLD"
            old = self.lines[:]
            self.state = "NONE"
            self.lines = []
            return ("FLUSH_BACK", old)

        if self.state == "TABLE":
            if "|" in stripped:
                self.lines.append(line)
                return "HOLD"
            table = self.lines[:]
            self.state = "NONE"
            self.lines = []
            return ("FLUSH_TABLE", table, line)

    def flush_tail(self):
        if self.state == "TABLE":
            table = self.lines[:]
            self.state = "NONE"
            self.lines = []
            return ("FLUSH_TABLE", table, None)
        return None

# ======================================================
# STREAM COLLECTOR
# ======================================================
class StreamCollector:
    def __init__(self):
        self.partial = ""
        self.table = TableState()
        self.full_text = ""

    def collect(self, response):
        for raw in response.iter_lines():
            if not raw or not raw.startswith("data: "):
                continue

            data = raw[6:]
            if data == "[DONE]":
                break

            chunk = json.loads(data)
            content = chunk["choices"][0]["delta"].get("content")
            if not content:
                continue

            self.partial += content
            self.full_text += content

            while "\n" in self.partial:
                line, self.partial = self.partial.split("\n", 1)
                result = self.table.feed(line)

                if result == "NO":
                    Renderer.prose(line)
                elif isinstance(result, tuple):
                    if result[0] == "FLUSH_BACK":
                        for l in result[1]:
                            Renderer.prose(l)
                        Renderer.prose(line)
                    elif result[0] == "FLUSH_TABLE":
                        Renderer.table("\n".join(result[1]))
                        if result[2]:
                            Renderer.prose(result[2])

        tail = self.table.flush_tail()
        if tail:
            Renderer.table("\n".join(tail[1]))

        if self.partial.strip():
            Renderer.prose(self.partial)

        return self.full_text
    
    def collect_text(self, text: str):
        """
        Process full text (non-stream) through the same rendering pipeline
        """
        self.partial = text
        self.full_text = text
        
        while "\n" in self.partial:
            line, self.partial = self.partial.split("\n", 1)
            result = self.table.feed(line)
            
            if result == "NO":
                Renderer.prose(line)
            elif isinstance(result, tuple):
                if result[0] == "FLUSH_BACK":
                    for l in result[1]:
                        Renderer.prose(l)
                    Renderer.prose(line)
                elif result[0] == "FLUSH_TABLE":
                    Renderer.table("\n".join(result[1]))
                    if result[2]:
                        Renderer.prose(result[2])
                        
        tail = self.table.flush_tail()
        if tail:
            Renderer.table("\n".join(tail[1]))
            
        if self.partial.strip():
            Renderer.prose(self.partial)

# ======================================================
# RAW HELPERS
# ======================================================
def stream_raw(response):
    for raw in response.iter_lines():
        if raw and raw.startswith("data: "):
            data = raw[6:]
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            content = chunk["choices"][0]["delta"].get("content")
            if content:
                sys.stdout.write(content)
                sys.stdout.flush()

def inferensi_raw(payload, endpoint, headers):
    with httpx.Client(timeout=60) as client:
        r = client.post(endpoint, headers=headers, json=payload)
        r.raise_for_status()
        print(r.json()["choices"][0]["message"]["content"])

# ======================================================
# ERROR HANDLING
# ======================================================

def handle_http_error(e: httpx.HTTPStatusError, endpoint: str, model: str):
    status = e.response.status_code
    reason = e.response.reason_phrase
    
    print()
    print(f"❌ Request failed (HTTP {status} {reason})")
    print()
    print("Possible causes:")
    if status == 401:
        print("- Invalid or missing API key")
    elif status == 404:
        print("- Endpoint not found")
        print("- Model name not recognized by server")
    elif status == 400:
        print("- Invalid request payload")
        print("- Model not supported by endpoint")
    elif status >= 500:
        print("- Server error on remote endpoint")
        
    print()
    print(f"Endpoint: {endpoint}")
    print(f"Model: {model}")
    print()
    print("Tip: check TERMINAL_CHAT_ENDPOINT, TERMINAL_CHAT_KEY, TERMINAL_CHAT_MODEL")
    print()

# ======================================================
# ENVIRONMENT STATUS
# ======================================================
def print_env_status():
    endpoint = os.environ.get("TERMINAL_CHAT_ENDPOINT")
    api_key = os.environ.get("TERMINAL_CHAT_KEY")
    model = os.environ.get("TERMINAL_CHAT_MODEL")
    
    print("\nEnvironment status:")
    
    print(f"  TERMINAL_CHAT_ENDPOINT = {endpoint or '<NOT SET>'}")
    print(f"  TERMINAL_CHAT_MODEL    = {model or '<NOT SET>'}")
    
    if api_key:
        masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        print(f"  TERMINAL_CHAT_KEY      = {masked}")
    else:
        print("  TERMINAL_CHAT_KEY      = <NOT SET>")
        
    print()

# ======================================================
# CONVERSATION PERSISTENCE (CRASH-SAFE)
# ======================================================
def load_conversation_history():
    """
    Load FULL stored conversation (bounded by store limit).
    Context slicing happens elsewhere.
    """
    if not os.path.exists(CONVERSATION_FILE):
        return []
    
    try:
        with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            return []
        
        return data[-CONVERSATION_STORE_LIMIT:]
    
    except Exception:
        return []
    
    
def save_conversation_history(messages):
    """
    Persist conversation incrementally.
    """
    try:
        trimmed = messages[-CONVERSATION_STORE_LIMIT:]
        with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
            json.dump(trimmed, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
        
        
# ======================================================
# INTERACTIVE
# ======================================================
class SessionConfig:
    def __init__(self, model, max_tokens, temperature, top_p, system_prompt, history):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.system_prompt = system_prompt
        self.history = history

class Conversation:
    def __init__(self, max_pairs):
        self.max_pairs = max_pairs
        self.messages = []

    def add(self, role, content):
        self.messages.append({"role": role, "content": content})
        self.messages = self.messages[-self.max_pairs * 2 :]

    def build(self, system_prompt):
        """
        Build context window for LLM (bounded by max_pairs),
        NOT full stored history.
        """
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
            
        msgs.extend(self.messages[-self.max_pairs * 2 :])
        return msgs

def read_multiline(prompt="| ", end_cmd="/end", cancel_cmd="/cancel"):
    print("(multiline mode — type /end to submit, /cancel to abort)")
    lines = []
    
    while True:
        try:
            line = input(prompt)
        except EOFError:
            return None
        
        cmd = line.strip()
        if cmd == cancel_cmd:
            print("(multiline aborted)")
            return None
        
        if cmd == end_cmd:
            break
        
        lines.append(line)
        
    return "\n".join(lines).rstrip()

def print_multiline_status(text):
    chars = len(text)
    lines = text.count("\n") + 1 if text else 0
    print(f"[multiline] {lines} lines, {chars} chars\n")
    
def interactive_loop(model, cfg, endpoint, headers):
    convo = Conversation(cfg.history)
    
    # LOAD persistent conversation history
    convo.messages = load_conversation_history()
    print(
        'Welcome to Terminal Chat v0.4.1.\n'
        'Type "/cmd help" to engage command or "/bye" to end chat.\n'
        'Use "/multiline" to enter multiline mode/paste large text, put "/end" in new line to send.\n'
        f'Conversation restored. '
        f'Storage cap {CONVERSATION_STORE_LIMIT} messages. '
        f'Context cap {cfg.history} pairs.\n'
    )
    
    while True:
        try:
            user = input("> ").strip()
            
            # ======================================================
            # EXIT
            # ======================================================
            if user == "/bye":
                save_conversation_history(convo.messages)
                print("\nbye 👋\n")
                break
            
            if not user:
                continue
            
            # ======================================================
            # COMMANDS
            # ======================================================
            if user.startswith("/cmd"):
                handle_cmd(user, cfg, convo)
                continue
            
            # ======================================================
            # EXPLICIT MULTILINE MODE (EXCLUSIVE)
            # ======================================================
            if user == "/multiline":
                content = read_multiline()
                if not content:
                    continue
                
                print_multiline_status(content)
                user = content
                
            # ======================================================
            # IMPLICIT MULTILINE (PASTE / MANUAL)
            # ======================================================
            elif "\n" in user:
                lines = [user.rstrip("\n")]
                while True:
                    line = input()
                    if line.strip() == "":
                        break
                    lines.append(line)
                    
                user = "\n".join(lines).rstrip()
                print_multiline_status(user)
                
            # ======================================================
            # FINAL SAFETY
            # ======================================================
            if not user:
                continue
            
            # ======================================================
            # SEND TO LLM
            # ======================================================
            convo.add("user", user)
            print()
            
            payload = {
                "model": cfg.model,
                "messages": convo.build(cfg.system_prompt),
                "max_tokens": cfg.max_tokens,
                "temperature": cfg.temperature,
                "top_p": cfg.top_p,
                "stream": True,
            }
            
            with httpx.Client(timeout=None) as client:
                try:
                    with client.stream(
                        "POST",
                        endpoint,
                        headers=headers,
                        json=payload
                    ) as r:
                        r.raise_for_status()
                        text = StreamCollector().collect(r)
                    
                except httpx.HTTPStatusError as e:
                    handle_http_error(e, endpoint, cfg.model)
                    return
                
                except httpx.RequestError as e:
                    print()
                    print("❌ Network error while connecting to endpoint")
                    print(f"Detail: {e}")
                    print()
                    return
                
            # COMPLETE PAIR
            convo.add("assistant", text)
            save_conversation_history(convo.messages)
            print()
            
        except EOFError:
            save_conversation_history(convo.messages)
            print("\nbye.")
            break

def handle_cmd(line, cfg, convo):
    parts = line.split(maxsplit=2)
    if len(parts) < 2:
        print("Usage: /cmd <option> <value>")
        return
    
    cmd = parts[1]
    val = parts[2] if len(parts) > 2 else None
    
    try:
        if cmd == "temperature":
            cfg.temperature = float(val)
        elif cmd == "top_p":
            cfg.top_p = float(val)
        elif cmd == "max_tokens":
            cfg.max_tokens = int(val)
        elif cmd == "history":
            convo.max_pairs = int(val)
            convo.messages = convo.messages[-convo.max_pairs * 2 :]
            save_conversation_history(convo.messages)
        elif cmd == "system_prompt":
            cfg.system_prompt = val
        elif cmd == "show":
            print({
                "max_tokens": cfg.max_tokens,
                "temperature": cfg.temperature,
                "top_p": cfg.top_p,
                "system_prompt": cfg.system_prompt,
                "history_pairs": convo.max_pairs,
            })
        elif cmd == "help":
            print(
                "/cmd temperature <float>\n"
                "/cmd top_p <float>\n"
                "/cmd max_tokens <int>\n"
                "/cmd history <int>\n"
                "/cmd system_prompt <text>\n"
                "/cmd show\n"
                "/cmd help"
            )
        elif cmd == "model":
            if not val:
                print("Usage: /cmd model <model_name>")
                return
            cfg.model = val
        else:
            print("Unknown command. Type /cmd help.")
    except Exception as e:
        print(f"Invalid value: {e}")

# ======================================================
# STDIN PIPE
# ======================================================

def read_stdin():
    """
    Read piped stdin with safety truncation.
    """
    if not sys.stdin.isatty():
        data = sys.stdin.read()
        if not data:
            return None
        
        data = data.strip()
        
        if len(data) > MAX_STDIN_CHARS:
            return (
                data[:MAX_STDIN_CHARS]
                + "\n\n[...STDIN TRUNCATED...]"
            )
        
        return data
    return None

# ======================================================
# CLI
# ======================================================
def main():
    p = argparse.ArgumentParser(
        "terminal-chat v0.4.0",
        description="Streaming AI chat CLI with rich terminal rendering",
    )
    
    p.add_argument("-p", "--prompt", help="One-shot prompt (CLI mode)")
    p.add_argument("-i", "--interactive", action="store_true", help="Interactive chat mode")
    p.add_argument("-m", "--model", help="Model name (override TERMINAL_CHAT_MODEL)")
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--system-prompt")
    p.add_argument("--history", type=int, default=4)
    p.add_argument("-r", "--raw", action="store_true")
    p.add_argument("--no-stream", action="store_true")
    p.add_argument("--style", choices=["rich", "plain", "clean"], default="rich")
    
    args = p.parse_args()
    
    # ======================================================
    # STYLE MODE
    # ======================================================
    global STYLE_MODE
    STYLE_MODE = args.style
    if args.style in ("plain", "clean"):
        TERM.disable_ansi()
        
    # ======================================================
    # READ STDIN (DEFINE EARLY)
    # ======================================================
    stdin_text = read_stdin()
    
    # ======================================================
    # NO-ARG HELP
    # ======================================================
    if len(sys.argv) == 1 and not stdin_text:
        p.print_help()
        print_env_status()
        sys.exit(0)
        
    # ======================================================
    # ENVIRONMENT VARIABLES
    # ======================================================
    endpoint = os.environ.get("TERMINAL_CHAT_ENDPOINT")
    api_key = os.environ.get("TERMINAL_CHAT_KEY")
    env_model = os.environ.get("TERMINAL_CHAT_MODEL")
    
    # ======================================================
    # MODEL RESOLUTION (ARG > ENV)
    # ======================================================
    model = args.model or env_model
    if not model:
        print("Error: No model specified.")
        print('Set TERMINAL_CHAT_MODEL or use --model or "/cmd model"')
        sys.exit(1)
        
    if not endpoint or not api_key:
        print("Error: TERMINAL_CHAT_ENDPOINT and TERMINAL_CHAT_KEY must be set.")
        sys.exit(1)
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    cfg = SessionConfig(
        model,
        args.max_tokens,
        args.temperature,
        args.top_p,
        args.system_prompt,
        args.history,
    )
    
    # ======================================================
    # INTERACTIVE MODE
    # ======================================================
    if args.interactive:
        interactive_loop(model, cfg, endpoint, headers)
        return
    
    # ======================================================
    # ONE-SHOT / PIPE MODE
    # ======================================================
    if stdin_text and args.prompt:
        user_content = f"[KONTEKS]:\n{stdin_text}\n\n[INPUT]:\n{args.prompt}"
    else:
        user_content = stdin_text or args.prompt
        
    messages = []
    if cfg.system_prompt:
        messages.append({"role": "system", "content": cfg.system_prompt})
    if user_content:
        messages.append({"role": "user", "content": user_content})
        
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": cfg.max_tokens,
        "temperature": cfg.temperature,
        "top_p": cfg.top_p,
        "stream": not args.no_stream,
    }
    
    with httpx.Client(timeout=None) as client:
        if args.raw:
            if args.no_stream:
                inferensi_raw(payload, endpoint, headers)
            else:
                with client.stream("POST", endpoint, headers=headers, json=payload) as r:
                    r.raise_for_status()
                    stream_raw(r)
        else:
            if args.no_stream:
                r = client.post(endpoint, headers=headers, json=payload)
                r.raise_for_status()
                StreamCollector().collect_text(
                    r.json()["choices"][0]["message"]["content"]
                )
            else:
                with client.stream("POST", endpoint, headers=headers, json=payload) as r:
                    r.raise_for_status()
                    StreamCollector().collect(r)

if __name__ == "__main__":
    main()