#!/usr/bin/env python3
import httpx
import json
import argparse
import shutil
import textwrap
import re
import sys
from prettytable import PrettyTable

# ======================================================
# CONFIG
# ======================================================
URL = "https://YOUR_API_ENDPOINT/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}

# ======================================================
# TERMINAL
# ======================================================
class Terminal:
    def __init__(self):
        self.width = shutil.get_terminal_size((80, 20)).columns
        self.ansi = sys.stdout.isatty()

    def color(self, code):
        return code if self.ansi else ""

TERM = Terminal()

ANSI_RESET = TERM.color("\033[0m")
ANSI_BOLD  = TERM.color("\033[1m")
ANSI_WHITE = TERM.color("\033[97m")
ANSI_GRAY  = TERM.color("\033[90m")

# ======================================================
# MARKDOWN → ANSI
# ======================================================
class Markdown:
    @staticmethod
    def style(text: str) -> str:
        text = re.sub(
            r"\*\*(.+?)\*\*",
            lambda m: f"{ANSI_BOLD}{ANSI_WHITE}{m.group(1)}{ANSI_RESET}",
            text
        )
        text = re.sub(
            r"\*(.+?)\*",
            lambda m: f"{ANSI_GRAY}{m.group(1)}{ANSI_RESET}",
            text
        )
        text = re.sub(
            r"^(\d+\.)",
            lambda m: f"{ANSI_BOLD}{m.group(1)}{ANSI_RESET}",
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
        styled = Markdown.style(line.rstrip("\n"))
        wrapped = textwrap.fill(
            styled,
            width=TERM.width,
            replace_whitespace=False,
            drop_whitespace=False
        )
        print(wrapped)

    @staticmethod
    def table(markdown_block: str):
        lines = [l.rstrip() for l in markdown_block.splitlines() if l.strip()]
        headers = [h.strip() for h in lines[0].strip("|").split("|")]
        
        rows = []
        for row in lines[2:]:
            if "|" not in row:
                continue
            rows.append([c.strip() for c in row.strip("|").split("|")])
            
        # === HITUNG LEBAR TERMINAL REAL-TIME ===
        term_width = shutil.get_terminal_size((80, 20)).columns
        col_count = len(headers)
        
        # margin + border estimation
        max_col_width = max(
            10,
            (term_width - (col_count + 1) * 3) // col_count
        )
        
        # === DETEKSI KOLOM NUMERIK ===
        def is_numeric_column(col_idx):
            for r in rows:
                v = re.sub(r"[,%\s]", "", r[col_idx])
                if not v.replace(".", "").isdigit():
                    return False
            return True
        
        numeric_cols = {
            idx for idx in range(col_count) if is_numeric_column(idx)
        }
        
        # === RENDER HEADER ===
        styled_headers = [Markdown.style(h) for h in headers]
        table = PrettyTable(styled_headers)
        
        for i, h in enumerate(styled_headers):
            table.max_width[h] = max_col_width
            table.align[h] = "r" if i in numeric_cols else "l"
            
        # === RENDER ROW ===
        for r in rows:
            rendered = []
            for idx, cell in enumerate(r):
                styled = Markdown.style(cell)
                wrapped = "\n".join(
                    textwrap.wrap(
                        styled,
                        width=max_col_width,
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
# STREAM COLLECTOR (RETURNS FULL TEXT)
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
                line = line.rstrip("\n")

                result = self.table.feed(line)

                if result == "NO":
                    Renderer.prose(line)
                elif result == "HOLD":
                    continue
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

# ======================================================
# SESSION CONFIG & MEMORY
# ======================================================
class SessionConfig:
    def __init__(self, max_tokens, temperature, top_p, system_prompt, history):
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
        self.trim()

    def trim(self):
        max_len = self.max_pairs * 2
        if len(self.messages) > max_len:
            self.messages = self.messages[-max_len:]

    def build(self, system_prompt):
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(self.messages)
        return msgs

# ======================================================
# INTERACTIVE
# ======================================================
def handle_cmd(line, cfg, convo):
    parts = line.split(maxsplit=2)
    if len(parts) < 2:
        return

    cmd = parts[1]
    val = parts[2] if len(parts) > 2 else None

    if cmd == "temperature":
        cfg.temperature = float(val)
    elif cmd == "top_p":
        cfg.top_p = float(val)
    elif cmd == "max_tokens":
        cfg.max_tokens = int(val)
    elif cmd == "history":
        convo.max_pairs = int(val)
        convo.trim()
    elif cmd == "system_prompt":
        cfg.system_prompt = val
    elif cmd == "show":
        print(cfg.__dict__)
    elif cmd == "help":
        print("/cmd temperature|top_p|max_tokens|history|system_prompt|show|help")
    else:
        print("unknown command")

def interactive_loop(model, cfg):
    convo = Conversation(cfg.history)
    print("Interactive mode. Type /cmd help\n")

    while True:
        try:
            user = input("> ").strip()
        except EOFError:
            print("\nbye.")
            break

        if not user:
            continue
        
        if user == "/bye":
            print("\nbye 👋")
            print("")
            break

        if user.startswith("/cmd"):
            handle_cmd(user, cfg, convo)
            continue

        convo.add("user", user)
        print()  # baris kosong sebelum respons model

        payload = {
            "model": model,
            "messages": convo.build(cfg.system_prompt),
            "max_tokens": cfg.max_tokens,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "stream": True
        }

        with httpx.Client(timeout=None) as client:
            with client.stream("POST", URL, headers=HEADERS, json=payload) as r:
                r.raise_for_status()
                text = StreamCollector().collect(r)

        convo.add("assistant", text)
        print()  # baris kosong setelah respons model

# ======================================================
# CLI
# ======================================================
def main():
    p = argparse.ArgumentParser("terminal-chat v0.2")
    p.add_argument("-p", "--prompt")
    p.add_argument("-i", "--interactive", action="store_true")
    p.add_argument("-m", "--model", default="tugasi-chat")
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--system-prompt")
    p.add_argument("--history", type=int, default=10)
    args = p.parse_args()

    cfg = SessionConfig(
        args.max_tokens,
        args.temperature,
        args.top_p,
        args.system_prompt,
        args.history
    )

    if args.interactive:
        interactive_loop(args.model, cfg)
    else:
        payload = {
            "model": args.model,
            "messages": (
                [{"role": "system", "content": cfg.system_prompt}] if cfg.system_prompt else []
            ) + [{"role": "user", "content": args.prompt}],
            "max_tokens": cfg.max_tokens,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "stream": runtime.stream
        }
        
        with httpx.Client(timeout=None) as client:
            if runtime.raw:
                if runtime.stream:
                    with client.stream("POST", endpoint, headers=headers, json=payload) as r:
                        r.raise_for_status()
                        stream_raw(r)
                else:
                    inferensi_raw(payload, endpoint, headers)
            else:
                if runtime.stream:
                    with client.stream("POST", endpoint, headers=headers, json=payload) as r:
                        r.raise_for_status()
                        StreamCollector().collect(r)
                else:
                    with client.post(endpoint, headers=headers, json=payload) as r:
                        r.raise_for_status()
                        text = r.json()["choices"][0]["message"]["content"]
                        Renderer.prose(text)

if __name__ == "__main__":
    main()
    