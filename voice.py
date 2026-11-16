import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SR = 16000
model = WhisperModel("medium", device="cpu", compute_type="int8")

HINT = ("Computer control commands. Click the text area and type hello world. "
        "Open Notepad. Press Control S. Scroll down. Select all. "
        "テキストエリアをクリックして入力して。")

def listen():
    input("Press Enter to START speaking...")
    frames = []

    def callback(indata, n, t, status):
        frames.append(indata.copy())

    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", callback=callback):
        input("Speaking... press Enter to STOP")

    audio = np.concatenate(frames).flatten()
    segments, info = model.transcribe(
        audio, language=None, vad_filter=True,
        beam_size=5, initial_prompt=HINT,
    )
    text = "".join(s.text for s in segments).strip()
    print(f"[{info.language}] {text}")
    
    return text

if __name__ == "__main__":
    listen()