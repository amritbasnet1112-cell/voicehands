import os
import re
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SR = 16000
ASR_MODEL = os.environ.get("VH_ASR_MODEL", "small")
ALLOWED_LANGS = ("en", "ja")
_model = None

HINTS = {
    "en": (
        "Desktop voice commands: click, button, icon, menu, window, type, "
        "press, hotkey, scroll, open, close, confirm, yes, no, cancel."
    ),
    "ja": (
        "パソコン音声操作コマンド。クリック、ボタン、アイコン、入力、押す、"
        "スクロール、開く、閉じる、確認、はい、いいえ、キャンセル。"
    ),
}

YES_WORDS = {
    "yes", "yeah", "yep", "confirm", "proceed", "ok", "okay", "approve", "do it",
    "はい", "うん", "実行", "いいよ", "オッケー", "オーケー", "お願い",
}


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(ASR_MODEL, device="cpu", compute_type="int8")
    return _model


def detect_en_ja(model, audio):
    _, _, probs = model.detect_language(audio)
    candidates = [(code, p) for code, p in probs if code in ALLOWED_LANGS]
    if not candidates:
        return "en"
    return max(candidates, key=lambda x: x[1])[0]


def listen_with_lang(start_prompt="Press Enter to START speaking..."):
    input(start_prompt)
    frames = []

    def callback(indata, n, t, status):
        frames.append(indata.copy())

    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", callback=callback):
        input("Speaking... press Enter to STOP")

    if not frames:
        return "", "en"

    audio = np.concatenate(frames).flatten()
    model = get_model()
    lang = detect_en_ja(model, audio)
    segments, _ = model.transcribe(
        audio, language=lang, vad_filter=True,
        beam_size=5, initial_prompt=HINTS[lang],
    )
    text = "".join(s.text for s in segments).strip()
    print(f"[{lang}] {text}")
    return text, lang


def listen():
    text, _ = listen_with_lang()
    return text


def is_affirmative(text):
    clean = re.sub(r"[.!?,。、！？\s]+", " ", text.lower()).strip()
    if clean in YES_WORDS:
        return True
    tokens = set(clean.split())
    return any(w in tokens or (not w.isascii() and w in clean) for w in YES_WORDS)


def confirm_voice(action):
    print(f"\n[SAFETY GATE] Risky action: {action}")
    text, lang = listen_with_lang("Say YES / はい to confirm, or NO / いいえ to cancel (press Enter to start)...")
    approved = is_affirmative(text)
    print(f"[SAFETY GATE] Heard '{text}' ({lang}) -> {'APPROVED' if approved else 'CANCELLED'}")
    return approved


if __name__ == "__main__":
    listen()