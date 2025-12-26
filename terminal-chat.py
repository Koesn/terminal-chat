#!/usr/bin/env python3

import os
import httpx
import json
import argparse
import shutil
import textwrap
import re
import sys
from prettytable import PrettyTable

# ======================================================
# TERMINAL
# ======================================================
class Terminal:
    def __init__(self):
        self.ansi = sys.stdout.isatty()

    def width(self):
        return shutil.get_terminal_size((80, 20)).columns

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
            width=TERM.width(),
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
            if "|" in row:
                rows.append([c.strip() for c in row.strip("|").split("|")])

        term_width = TERM.width()
        col_count = len(headers)
        max_col_width = max(10, (term_width - (col_count + 1) * 3) // col_count)

        def is_numeric_column(idx):
            for r in rows:
                v = re.sub(r"[,%\s]", "", r[idx])
                if not v.replace(".", "").isdigit():
                    return False
            return True

        numeric_cols = {i for i in range(col_count) if is_numeric_column(i)}

        styled_headers = [Markdown.style(h) for h in headers]
        table = PrettyTable(styled_headers)

        for i, h in enumerate(styled_headers):
            table.align[h] = "r" if i in numeric_cols else "l"
            table.max_width[h] = max_col_width

        for r in rows:
            rendered = []
            for cell in r:
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
# INTERACTIVE
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
        self.messages = self.messages[-self.max_pairs * 2 :]

    def build(self, system_prompt):
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(self.messages)
        return msgs

def interactive_loop(model, cfg, endpoint, headers):
    convo = Conversation(cfg.history)
    print("Interactive mode. Type /cmd help or /bye\n")

    while True:
        try:
            user = input("> ").strip()
        except EOFError:
            print("\nbye.")
            break

        if user == "/bye":
            print("\nbye 👋\n")
            break

        if not user:
            continue

        if user.startswith("/cmd"):
            print("Use CLI args for config in interactive.")
            continue

        convo.add("user", user)
        print()

        payload = {
            "model": model,
            "messages": convo.build(cfg.system_prompt),
            "max_tokens": cfg.max_tokens,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "stream": True,
        }

        with httpx.Client(timeout=None) as client:
            with client.stream("POST", endpoint, headers=headers, json=payload) as r:
                r.raise_for_status()
                text = StreamCollector().collect(r)

        convo.add("assistant", text)
        print()

# ======================================================
# CLI
# ======================================================
def main():
    p = argparse.ArgumentParser(
        "chat-cli v0.3",
        description="Streaming AI chat CLI with rich terminal rendering",
    )

    p.add_argument("-p", "--prompt", help="One-shot prompt (CLI mode)")
    p.add_argument("-i", "--interactive", action="store_true", help="Interactive chat mode")
    p.add_argument("-m", "--model", default="tugasi-chat", help="Model name")
    p.add_argument("--max-tokens", type=int, default=4096, help="Max tokens")
    p.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    p.add_argument("--top-p", type=float, default=0.95, help="Top-p sampling")
    p.add_argument("--system-prompt", help="System prompt")
    p.add_argument("--history", type=int, default=10, help="History pairs (interactive)")
    p.add_argument("-r", "--raw", action="store_true", help="Raw output (CLI only)")
    p.add_argument("--no-stream", action="store_true", help="Disable streaming (CLI only)")

    args = p.parse_args()

    if len(sys.argv) == 1:
        p.print_help()
        sys.exit(0)

    endpoint = os.environ.get("CHAT_CLI_ENDPOINT")
    api_key = os.environ.get("CHAT_CLI_KEY")

    if not endpoint or not api_key:
        print("Error: CHAT_CLI_ENDPOINT and CHAT_CLI_KEY must be set")
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    cfg = SessionConfig(
        args.max_tokens,
        args.temperature,
        args.top_p,
        args.system_prompt,
        args.history,
    )

    if args.interactive:
        interactive_loop(args.model, cfg, endpoint, headers)
        return

    payload = {
        "model": args.model,
        "messages": (
            [{"role": "system", "content": cfg.system_prompt}] if cfg.system_prompt else []
        ) + [{"role": "user", "content": args.prompt}],
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
                
                text = r.json()["choices"][0]["message"]["content"]
                StreamCollector().collect_text(text)
            else:
                with client.stream("POST", endpoint, headers=headers, json=payload) as r:
                    r.raise_for_status()
                    StreamCollector().collect(r)

if __name__ == "__main__":
    main()