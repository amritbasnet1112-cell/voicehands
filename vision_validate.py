import os, time, subprocess
import pyautogui
from PIL import ImageGrab, Image
from pywinauto import Desktop
from vision_check import find_truth, COLORS
from scale_check import ask_image

PAGE_DIR = os.path.abspath("benchmark/pages")
PAGE = os.path.join(PAGE_DIR, "hard2.html")
TITLE_RE = r"VH Hard Page 2.*Edge"
IN_W = 1176

HTML2 = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>VH Hard Page 2</title>
<style>
  body { margin: 0; font-family: sans-serif; }
  .sq { position: absolute; width: 110px; height: 110px; border-radius: 12px; cursor: pointer; }
  canvas { position: absolute; left: 800px; top: 420px; border: 2px solid #888; cursor: pointer; }
</style>
</head>
<body>
<h1 style="position:absolute; left:60px; top:30px">VoiceHands hard page 2</h1>
<div class="sq" style="left:640px; top:260px; background:#e53935" onclick="hit('red')"></div>
<div class="sq" style="left:120px; top:330px; background:#43a047" onclick="hit('green')"></div>
<div class="sq" style="left:380px; top:480px; background:#1e88e5" onclick="hit('blue')"></div>
<canvas id="c" width="320" height="200" onclick="hit('canvas')"></canvas>
<script>
function hit(what) { document.title = 'CLICKED:' + what; }
var ctx = document.getElementById('c').getContext('2d');
ctx.fillStyle = '#fdd835';
ctx.beginPath(); ctx.arc(160, 100, 70, 0, 6.283); ctx.fill();
</script>
</body>
</html>
"""

def main():
    os.makedirs(PAGE_DIR, exist_ok=True)
    with open(PAGE, "w", encoding="utf-8") as f:
        f.write(HTML2)
    url = "file:///" + PAGE.replace("\\", "/")
    subprocess.Popen(["cmd", "/c", "start", "", "msedge", "--new-window", url])
    print("Opening page 2 in a new Edge window...")
    time.sleep(7)
    try:
        win = Desktop(backend="uia").window(title_re=TITLE_RE, found_index=0)
        win.set_focus()
        time.sleep(0.8)
    except Exception as e:
        print("Could not find the page 2 window:", e)
        return

    r = win.rectangle()
    sw, sh = pyautogui.size()
    full = ImageGrab.grab().size
    left, top = max(r.left, 0), max(r.top, 0)
    right, bottom = min(r.right, sw), min(r.bottom, sh)
    shot = ImageGrab.grab(bbox=(left, top, right, bottom)).convert("RGB")
    w0, h0 = shot.size
    print(f"pyautogui screen: {sw}x{sh} | full screenshot: {full[0]}x{full[1]} | window crop: {w0}x{h0}")

    H = max(28, round(h0 * IN_W / w0 / 28) * 28)
    img = shot.resize((IN_W, H), Image.LANCZOS)
    img.save("logs/vision2_in.png")
    sx, sy = w0 / IN_W, h0 / H
    print(f"model input: {IN_W}x{H}")

    truth = find_truth(img)
    answers = ask_image(img)

    print(f"\n{'shape':<15}{'truth':<14}{'model':<14}{'miss on screen':<18}inside the shape?")
    hits = 0
    for name in COLORS:
        t, m = truth.get(name), answers.get(name)
        if t is None or m is None:
            print(f"{name:<15}missing (truth found: {t is not None}, model answered: {m is not None})")
            continue
        x0, y0, x1, y1 = t["box"]
        inside = x0 <= m[0] <= x1 and y0 <= m[1] <= y1
        hits += inside
        ex, ey = (m[0] - t["cx"]) * sx, (m[1] - t["cy"]) * sy
        s_t = f"({t['cx']:.0f},{t['cy']:.0f})"
        s_m = f"({m[0]:.0f},{m[1]:.0f})"
        s_e = f"({ex:+.0f},{ey:+.0f}) px"
        print(f"{name:<15}{s_t:<14}{s_m:<14}{s_e:<18}{inside}")
    print(f"inside the right shape: {hits}/{len(COLORS)}")

    try:
        win.close()
    except Exception:
        print("Please close the 'VH Hard Page 2' window yourself.")

if __name__ == "__main__":
    main()