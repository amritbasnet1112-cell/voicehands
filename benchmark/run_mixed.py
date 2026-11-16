import sys, os, re, json, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyautogui
from PIL import ImageGrab, Image
from pywinauto import Desktop
from run_vision import ask_target, IN_W, TOP_FRAC

PAGE_DIR = os.path.abspath("benchmark/pages")
PAGE = os.path.join(PAGE_DIR, "mixed.html")
TARGET = r"(VH Mixed Page|CLICKED).*Edge"
TAG = os.environ.get("VH_TAG", "dev")
LABELS = {"uia": "uia-rules", "vision": "vision-7b", "hybrid": "hybrid"}
CLICKABLE = ("Button", "Hyperlink", "MenuItem", "CheckBox", "RadioButton",
             "TabItem", "ListItem", "Edit")

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>VH Mixed Page</title>
<style>
  body { margin: 0; font-family: sans-serif; }
  button { position: absolute; width: 150px; height: 60px; font-size: 22px; }
  .sq { position: absolute; width: 110px; height: 110px; border-radius: 12px; cursor: pointer; }
</style>
</head>
<body>
<h1 style="position:absolute; left:60px; top:30px">VoiceHands mixed page</h1>
<button style="left:80px; top:240px" onclick="hit('alpha')">Alpha</button>
<button style="left:300px; top:240px" onclick="hit('beta')">Beta</button>
<button style="left:520px; top:240px" onclick="hit('gamma')">Gamma</button>
<div class="sq" style="left:100px; top:420px; background:#e53935" onclick="hit('red')"></div>
<div class="sq" style="left:320px; top:420px; background:#43a047" onclick="hit('green')"></div>
<div class="sq" style="left:540px; top:420px; background:#1e88e5" onclick="hit('blue')"></div>
<script>function hit(w) { document.title = 'CLICKED:' + w; }</script>
</body>
</html>
"""

TASKS = [
    {"id": "m01", "goal": "Click the Alpha button", "expect": "alpha"},
    {"id": "m02", "goal": "Click the Beta button", "expect": "beta"},
    {"id": "m03", "goal": "Click the Gamma button", "expect": "gamma"},
    {"id": "m04", "goal": "Click the red square", "expect": "red"},
    {"id": "m05", "goal": "Click the green square", "expect": "green"},
    {"id": "m06", "goal": "Click the blue square", "expect": "blue"},
]

def find_window():
    return Desktop(backend="uia").window(title_re=TARGET, found_index=0)

def exists():
    try:
        find_window().wrapper_object()
        return True
    except Exception:
        return False

def open_page():
    os.makedirs(PAGE_DIR, exist_ok=True)
    with open(PAGE, "w", encoding="utf-8") as f:
        f.write(HTML)
    url = "file:///" + PAGE.replace("\\", "/")
    subprocess.Popen(["cmd", "/c", "start", "", "msedge", "--new-window", url])
    time.sleep(7)

def close_page():
    try:
        find_window().close()
        time.sleep(1.5)
    except Exception as e:
        print("close() failed:", e)
    if exists():
        try:
            find_window().set_focus()
            time.sleep(0.5)
            title = Desktop(backend="uia").window(active_only=True).window_text()
            if re.match(TARGET, title):
                pyautogui.hotkey("ctrl", "w")
                time.sleep(1.5)
        except Exception as e:
            print("Could not close the test window:", e)

def page_title():
    try:
        return find_window().window_text()
    except Exception:
        return ""

def clicked_value(title):
    m = re.match(r"CLICKED:(.*?)( - |$)", title)
    return m.group(1) if m else None

def active_ok():
    t = Desktop(backend="uia").window(active_only=True).window_text()
    return bool(re.match(TARGET, t)), t

def window_box(win):
    r = win.rectangle()
    sw, sh = pyautogui.size()
    return max(r.left, 0), max(r.top, 0), min(r.right, sw), min(r.bottom, sh)

def uia_resolve(win, goal, box):
    """Find a clickable element whose accessible name appears in the goal."""
    left, top, right, bottom = box
    limit = top + TOP_FRAC * (bottom - top)   # skip the browser toolbar
    g = goal.lower()
    best = None
    for el in win.descendants():
        try:
            if not el.is_visible():
                continue
            info = el.element_info
            name = (info.name or "").strip()
            if len(name) < 3 or name.lower() not in g:
                continue
            if str(info.control_type) not in CLICKABLE:
                continue
            r = el.rectangle()
            cx, cy = (r.left + r.right) // 2, (r.top + r.bottom) // 2
            if not (left <= cx <= right and limit <= cy <= bottom):
                continue
            if best is None or len(name) > len(best[0]):
                best = (name, cx, cy)
        except Exception:
            continue
    return best

def vision_click(goal, box):
    left, top, right, bottom = box
    shot = ImageGrab.grab(bbox=box).convert("RGB")
    w0, h0 = shot.size
    H = max(28, round(h0 * IN_W / w0 / 28) * 28)
    img = shot.resize((IN_W, H), Image.LANCZOS)
    x, y, raw = ask_target(img, goal)
    print("Model answer:", raw.replace("\n", " ")[:160])
    if x is None:
        return False, "vision:no-answer"
    if not (0 <= x <= IN_W and TOP_FRAC * H <= y <= H):
        return False, f"vision:refused ({x:.0f},{y:.0f})"
    ok, active = active_ok()
    if not ok:
        return False, f"vision:wrong-window {active}"
    rx, ry = left + x * w0 / IN_W, top + y * h0 / H
    pyautogui.click(int(rx), int(ry))
    time.sleep(1.0)
    return True, f"vision:click({rx:.0f},{ry:.0f})"

def solve(mode, goal):
    win = find_window()
    win.set_focus()
    time.sleep(0.8)
    box = window_box(win)
    if mode in ("uia", "hybrid"):
        hit = uia_resolve(win, goal, box)
        if hit:
            name, cx, cy = hit
            ok, active = active_ok()
            if not ok:
                return False, f"uia:wrong-window {active}"
            pyautogui.click(cx, cy)
            time.sleep(1.0)
            return True, f"uia:{name}@({cx},{cy})"
        if mode == "uia":
            return False, "uia:no-match"
    return vision_click(goal, box)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in LABELS:
        print("Usage: python benchmark\\run_mixed.py <uia|vision|hybrid> [trials] [task ids]")
        sys.exit(1)
    trials = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    only = sys.argv[3:]
    print("Mode:", mode, "| Tag:", TAG, "| page: mixed")
    if exists():
        print("A 'VH Mixed Page' window is already open. Close it and run again.")
        sys.exit(1)
    with open("logs/benchmark.jsonl", "a", encoding="utf-8") as out:
        for task in TASKS:
            if only and task["id"] not in only:
                continue
            for trial in range(trials):
                open_page()
                if not exists():
                    print("SKIPPED (test page did not open):", task["id"])
                    continue
                t0 = time.time()
                try:
                    finished, action = solve(mode, task["goal"])
                except pyautogui.FailSafeException:
                    print("FAILSAFE: stopped by mouse in screen corner")
                    raise
                except Exception as e:
                    finished, action = False, f"error:{e}"
                    print("ERROR:", e)
                secs = round(time.time() - t0, 1)
                got = clicked_value(page_title())
                ok = got == task["expect"]
                rec = {"tag": TAG, "mode": mode, "page": "mixed", "model": LABELS[mode],
                       "task": task["id"], "trial": trial, "finished": finished,
                       "success": ok, "expected": task["expect"],
                       "got": got if got is not None else "(nothing clicked)",
                       "seconds": secs, "actions": [action]}
                print("RESULT:", rec)
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                close_page()
    print("BENCHMARK COMPLETE")