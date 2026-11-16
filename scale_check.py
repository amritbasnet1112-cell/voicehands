import io, re, json, time
import numpy as np
import ollama
from PIL import Image
from vision_check import find_truth, COLORS, VLM

SRC = "logs/vision_in.png"
WIDTHS = [476, 1176]
PROMPT = ("Locate the red square, the green square, the blue square and the yellow circle "
          "in this image. Output the bounding box of each one in JSON format, like "
          '[{"bbox_2d": [x1, y1, x2, y2], "label": "red square"}].')

def ask_image(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    t0 = time.time()
    out = ollama.chat(model=VLM, options={"temperature": 0},
                      messages=[{"role": "user", "content": PROMPT, "images": [buf.getvalue()]}])
    print(f"  model call took {time.time() - t0:.0f} s")
    text = out["message"]["content"]
    answers = {}
    for chunk in re.findall(r"\{[^{}]*\}", text):
        try:
            obj = json.loads(chunk)
            box = [float(v) for v in obj.get("bbox_2d")]
            label = str(obj.get("label", "")).lower()
        except Exception:
            continue
        if len(box) != 4:
            continue
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        for name in COLORS:
            if name.split("_")[0] in label or (name == "yellow_circle" and "circle" in label):
                answers[name] = (cx, cy)
    return answers

if __name__ == "__main__":
    src = Image.open(SRC).convert("RGB")
    w0, h0 = src.size
    print("Source image:", src.size)
    for W in WIDTHS:
        H = max(28, round(h0 * W / w0 / 28) * 28)
        img = src.resize((W, H), Image.LANCZOS)
        truth = find_truth(img)
        print(f"\nInput {W}x{H}")
        answers = ask_image(img)
        rx, ry = [], []
        for name in COLORS:
            t, m = truth.get(name), answers.get(name)
            if t is None or m is None:
                print(f"  {name}: missing")
                continue
            print(f"  {name:<14}truth ({t['cx']:.0f},{t['cy']:.0f})  model ({m[0]:.0f},{m[1]:.0f})")
            rx.append(m[0] / t["cx"])
            ry.append(m[1] / t["cy"])
        if rx:
            print(f"  scale model/truth: x {np.mean(rx):.2f}, y {np.mean(ry):.2f}")