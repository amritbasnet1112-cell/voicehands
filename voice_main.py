import json
from voice import listen
from main import run

TARGET = ".*- Notepad"

if __name__ == "__main__":
    text = listen()
    with open("logs/asr.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"heard": text}, ensure_ascii=False) + "\n")
    if input(f"Run this command? '{text}' (y/n) ").lower() == "y":
        run(text, TARGET)