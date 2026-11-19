import sys, os, re, json, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VH_MAX_ITEMS", "80")

import pyautogui
from pywinauto import Desktop
from run_hard import log_len, actions_since
from main import run

PAGE_DIR = os.path.abspath("benchmark/pages")
PAGE = os.path.join(PAGE_DIR, "mixed2.html")
TARGET = r"(VH Unseen Page|CLICKED).*Edge"
TAG = os.environ.get("VH_TAG", "unseen1")
MODEL = os.environ.get("VH_MODEL", "qwen2.5:7b")

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>VH Unseen Page</title>
<style>
  body { margin: 0; font-family: sans-serif; }
  .dot { position: absolute; width: 110px; height: 110px; border-radius: 50%; cursor: pointer; }
  button { position: absolute; width: 150px; height: 60px; font-size: 22px; }
</style>
</head>
<body>
<h1 style="position:absolute; left:60px; top:30px">VoiceHands unseen page</h1>
<div class="dot" style="left:140px; top:200px; background:#fb8c00" onclick="hit('orange')"></div>
<div class="dot" style="left:380px; top:200px; background:#8e24aa" onclick="hit('purple')"></div>
<div class="dot" style="left:620px; top:200px; background:#fdd835; border:2px solid #f57f17" onclick="hit('yellow')"></div>
<button style="left:120px; top:410px" onclick="hit('filter')">Filter</button>
<button style="left:360px; top:410px" onclick="hit('details')">Details</button>
<button style="left:600px; top:410px" onclick="hit('refresh')">Refresh</button>
<script>function hit(w) { document.title = 'CLICKED:' + w; }</script>
</body>
</html>
"""

TASKS = [
    {"id": "u01", "goal": "Click the Filter button", "expect": "filter"},
    {"id": "u02", "goal": "Click the Details button", "expect": "details"},
    {"id": "u03", "goal": "Click the Refresh button", "expect": "refresh"},
    {"id": "u04", "goal": "Click the orange circle", "expect": "orange"},
    {"id": "u05", "goal": "Click the purple circle", "expect": "purple"},
    {"id": "u06", "goal": "Click the yellow circle", "expect": "yellow"},
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

if __name__ == "__main__":
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    only = sys.argv[2:]
    print("Model:", MODEL, "| Tag:", TAG, "| planner loop | page: mixed2 (unseen)")
    if exists():
        print("A 'VH Unseen Page' window is already open. Close it and run again.")
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
                start = log_len()
                t0 = time.time()
                try:
                    finished = run(task["goal"], TARGET)
                except pyautogui.FailSafeException:
                    print("FAILSAFE: stopped by mouse in screen corner")
                    raise
                except Exception as e:
                    finished = False
                    print("ERROR:", e)
                secs = round(time.time() - t0, 1)
                got = clicked_value(page_title())
                rec = {"tag": TAG, "mode": "loop", "page": "mixed2",
                       "model": MODEL, "task": task["id"], "trial": trial,
                       "finished": finished, "success": got == task["expect"],
                       "expected": task["expect"],
                       "got": got if got is not None else "(nothing clicked)",
                       "seconds": secs, "actions": actions_since(start)}
                print("RESULT:", rec)
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                close_page()
    print("BENCHMARK COMPLETE")