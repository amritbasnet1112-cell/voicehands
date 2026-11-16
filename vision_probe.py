import os, time, json, subprocess
import pyautogui
import ollama
from PIL import ImageGrab, ImageDraw
from pywinauto import Desktop
from hard_probe import HTML, PAGE, PAGE_DIR, TITLE_RE

VLM = os.environ.get("VH_VLM", "qwen2.5vl:7b")
TARGET_W = 952   # a multiple of 28, which this vision model works best with

def to_xy(v):
    try:
        if isinstance(v, dict):
            return float(v["x"]), float(v["y"])
        if isinstance(v, (list, tuple)):
            if len(v) == 4:
                return (float(v[0]) + float(v[2])) / 2, (float(v[1]) + float(v[3])) / 2
            if len(v) >= 2:
                return float(v[0]), float(v[1])
    except Exception:
        pass
    return None

def main():
    os.makedirs(PAGE_DIR, exist_ok=True)
    with open(PAGE, "w", encoding="utf-8") as f:
        f.write(HTML)
    url = "file:///" + PAGE.replace("\\", "/")
    subprocess.Popen(["cmd", "/c", "start", "", "msedge", "--new-window", url])
    print("Opening the hard page in a new Edge window...")
    time.sleep(7)

    win = Desktop(backend="uia").window(title_re=TITLE_RE, found_index=0)
    win.set_focus()
    time.sleep(0.8)
    r = win.rectangle()
    sw, sh = pyautogui.size()
    left, top = max(r.left, 0), max(r.top, 0)
    right, bottom = min(r.right, sw), min(r.bottom, sh)

    shot = ImageGrab.grab(bbox=(left, top, right, bottom)).convert("RGB")
    w0, h0 = shot.size
    W = TARGET_W
    H = max(28, round(h0 * W / w0 / 28) * 28)
    small = shot.resize((W, H))
    small.save("logs/vision_in.png")
    sx, sy = w0 / W, h0 / H

    prompt = (f"This is a screenshot, {W} pixels wide and {H} pixels tall. "
              "Find these four things on the web page: the red square, the green square, "
              "the blue square and the yellow circle. For each one, give the pixel "
              "coordinates of its center in this image, with (0, 0) at the top-left corner. "
              'Reply with JSON only, in this form: '
              '{"red": [x, y], "green": [x, y], "blue": [x, y], "yellow_circle": [x, y]}')
    with open("logs/vision_in.png", "rb") as f:
        img = f.read()

    print(f"Asking {VLM}. This can take several minutes on a laptop CPU...")
    t0 = time.time()
    out = ollama.chat(model=VLM, format="json", options={"temperature": 0},
                      messages=[{"role": "user", "content": prompt, "images": [img]}])
    print(f"Model call took {time.time() - t0:.0f} s")
    raw = out["message"]["content"]
    print("Raw answer:", raw)
    try:
        data = json.loads(raw)
    except Exception:
        print("The answer was not valid JSON.")
        return
    if not isinstance(data, dict):
        print("The answer was not a JSON object.")
        return

    draw = ImageDraw.Draw(small)
    for name in ("red", "green", "blue", "yellow_circle"):
        xy = to_xy(data.get(name))
        if xy is None:
            print(f"{name}: no coordinates in the answer")
            continue
        x, y = xy
        rx, ry = left + x * sx, top + y * sy
        print(f"{name}: model says ({x:.0f}, {y:.0f}) in the image -> screen ({rx:.0f}, {ry:.0f})")
        draw.ellipse((x - 12, y - 12, x + 12, y + 12), outline="magenta", width=3)
        draw.text((x + 16, y - 8), name, fill="magenta")
        pyautogui.moveTo(int(rx), int(ry), duration=0.6)
        time.sleep(2.5)
    small.save("logs/vision_probe.png")
    print("Saved logs/vision_probe.png (marked) and logs/vision_in.png (what the model saw)")

if __name__ == "__main__":
    main()