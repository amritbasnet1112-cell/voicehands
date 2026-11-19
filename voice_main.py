import json
import sys
from voice import listen_with_lang, confirm_voice
from main import run

DEFAULT_TARGET = ".*- Notepad"


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TARGET
    print(f"VoiceHands ready (target window: {target})")
    text, lang = listen_with_lang()
    with open("logs/asr.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"lang": lang, "heard": text, "target": target}, ensure_ascii=False) + "\n")
    if not text:
        print("Nothing heard, exiting.")
        sys.exit(0)
    run(text, target, confirm_fn=confirm_voice)