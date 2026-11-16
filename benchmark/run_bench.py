import sys, os, json, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyautogui, pyperclip
from pywinauto import Desktop
from main import run

SCRATCH = os.path.abspath("logs/bench_scratch.txt")
TARGET = r".*bench_scratch\.txt.*Notepad"
MODEL = os.environ.get("VH_MODEL", "qwen2.5:7b")
TAG = os.environ.get("VH_TAG", "dev")
RUN_LOG = "logs/run.jsonl"

TASKS = [
    {"id": "t01", "goal": "Click the text area and type hello world", "expect": "hello world"},
    {"id": "t02", "goal": "Click the text area and type good morning", "expect": "good morning"},
    {"id": "t03", "goal": "Click the text area and type こんにちは", "expect": "こんにちは"},
    {"id": "t04", "goal": "Click the text area and type VoiceHands", "expect": "VoiceHands"},
    {"id": "t05", "goal": "Click the text area and type 12345", "expect": "12345"},
    {"id": "t06", "goal": "Click the text area, type line one, press enter, then type line two",
     "expect": "line one\nline two"},
    {"id": "t07", "goal": "Click the text area, select all text with ctrl+a, then type new text",
     "setup": "old text", "expect": "new text"},
    {"id": "t08", "goal": "Click the text area, select all text with ctrl+a, then press delete",
     "setup": "delete me", "expect": ""},
]

def find_notepad():
    return Desktop(backend="uia").window(title_re=r".*Notepad", found_index=0)

def open_scratch():
    with open(SCRATCH, "w", encoding="utf-8") as f:
        f.write("")
    subprocess.Popen(["notepad.exe", SCRATCH])
    time.sleep(4)

def focus_scratch():
    find_notepad().set_focus()
    time.sleep(0.6)
    if "bench_scratch.txt" not in find_notepad().window_text():
        try:
            tab = find_notepad().child_window(title_re=r"bench_scratch.*", control_type="TabItem")
            tab.click_input()
            time.sleep(0.8)
        except Exception as e:
            print("Could not click the scratch tab:", e)
    title = Desktop(backend="uia").window(active_only=True).window_text()
    if "bench_scratch.txt" not in title:
        raise RuntimeError(f"Scratch tab is not active (active: {title!r}). Stopping to protect other tabs.")
    # Click into the text area so keystrokes go to the text, not the tab strip.
    r = find_notepad().rectangle()
    pyautogui.click((r.left + r.right) // 2, (r.top + r.bottom) // 2)
    time.sleep(0.3)

def read_text():
    focus_scratch()
    pyperclip.copy("")
    pyautogui.hotkey("ctrl", "a")
    pyautogui.hotkey("ctrl", "c")
    time.sleep(0.3)
    return pyperclip.paste().replace("\r\n", "\n").strip()

def reset(setup=None):
    for attempt in range(2):
        focus_scratch()
        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("delete")
        time.sleep(0.3)
        if setup:
            pyperclip.copy(setup)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.3)
        if read_text() == (setup or ""):
            return True
    return False

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
    print("Model:", MODEL, "| Tag:", TAG)
    open_scratch()
    with open("logs/benchmark.jsonl", "a", encoding="utf-8") as out:
        for task in TASKS:
            if only and task["id"] not in only:
                continue
            for trial in range(trials):
                if not reset(task.get("setup")):
                    print("SKIPPED (setup failed):", task["id"])
                    continue
                start = log_len()
                t0 = time.time()
                try:
                    finished = run(task["goal"], TARGET)
                except Exception as e:
                    finished = False
                    print("ERROR:", e)
                secs = round(time.time() - t0, 1)
                got = read_text()
                ok = got == task["expect"]
                rec = {"tag": TAG, "model": MODEL, "task": task["id"], "trial": trial,
                       "finished": finished, "success": ok,
                       "expected": task["expect"], "got": got, "seconds": secs,
                       "actions": actions_since(start)}
                print("RESULT:", rec)
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
    print("BENCHMARK COMPLETE")