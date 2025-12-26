#!/usr/bin/env python3

import httpx
import json
import argparse

URL = "https://YOUR_API_ENDPOINT/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}

def inferensi_teks(teks, model, stream=True):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": teks}],
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 0.95,
        "stream": stream
    }

    # ===============================
    # STREAMING MODE
    # ===============================
    if stream:
        with httpx.Client(timeout=None) as client:
            with client.stream("POST", URL, headers=HEADERS, json=payload) as response:
                if response.status_code != 200:
                    raise RuntimeError(f"HTTP {response.status_code}: {response.text}")

                for line in response.iter_lines():
                    if not line:
                        continue

                    if line.startswith("data: "):
                        data = line[6:]

                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0]["delta"]
                            content = delta.get("content")
                            if content:
                                print(content, end="", flush=True)
                        except Exception:
                            continue

                print()
                return None

    # ===============================
    # NON-STREAM MODE
    # ===============================
    else:
        with httpx.Client(timeout=60) as client:
            response = client.post(URL, headers=HEADERS, json=payload)

            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text}")

            result = response.json()
            return result["choices"][0]["message"]["content"]


def main():
    parser = argparse.ArgumentParser("OpenAI-compatible chat client")
    parser.add_argument("-m", "--model", default="tugasi-chat")
    parser.add_argument("-p", "--prompt", required=True)
    parser.add_argument("--no-stream", action="store_true")

    args = parser.parse_args()

    result = inferensi_teks(
        teks=args.prompt,
        model=args.model,
        stream=not args.no_stream
    )

    if result:
        print(result)


if __name__ == "__main__":
    main()
