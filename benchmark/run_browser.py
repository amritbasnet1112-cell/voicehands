import sys, os, re, json, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VH_MAX_ITEMS", "80")

import pyautogui
from pywinauto import Desktop
from browser_probe import HTML, PAGE, PAGE_DIR
from main import run

# Only our test window can match this: its title is "VH Test Page" or "SUBMITTED:...".
TARGET = r"(VH Test Page|SUBMITTED).*Edge"
MODEL = os.environ.get("VH_MODEL", "qwen2.5:7b")
TAG = os.environ.get("VH_TAG", "dev")
RUN_LOG = "logs/run.jsonl"

TASKS = [
    {"id": "b01", "goal": "Click the name box, type Amrit, then click the Submit button",
     "expect": "Amrit"},
    {"id": "b02", "goal": "Click the Submit button", "expect": ""},
    {"id": "b03", "goal": "Click the name box, type こんにちは, then click the Submit button",
     "expect": "こんにちは"},
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

def submitted_value(title):
    m = re.match(r"SUBMITTED:(.*?)( - |$)", title)
    return m.group(1) if m else None

def log_len():
    if not os.path.exists(RUN_LOG):
        return 0
    with open(RUN_LOG, encoding="utf-8") as f:
        return sum(1 for _ in f)

def actions_since(start):
    with open(RUN_LOG, encoding="utf-8") as f:
        lines = f.readlines()[start:]
    out = []
    for l in lines:
        a = json.loads(l)["action"]
        detail = a.get("text") or a.get("keys") or a.get("id") or ""
        if isinstance(detail, list):
            detail = "+".join(detail)
        out.append(f"{a.get('action')}:{detail}")
    return out

if __name__ == "__main__":
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    only = sys.argv[2:]
    print("Model:", MODEL, "| Tag:", TAG, "| mode: UIA-only")
    if exists():
        print("A 'VH Test Page' window is already open. Close it and run again.")
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
                except Exception as e:
                    finished = False
                    print("ERROR:", e)
                secs = round(time.time() - t0, 1)
                got = submitted_value(page_title())
                ok = got == task["expect"]
                rec = {"tag": TAG, "mode": "uia", "model": MODEL, "task": task["id"],
                       "trial": trial, "finished": finished, "success": ok,
                       "expected": task["expect"],
                       "got": got if got is not None else "(not submitted)",
                       "seconds": secs, "actions": actions_since(start)}
                print("RESULT:", rec)
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                close_page()
    print("BENCHMARK COMPLETE")