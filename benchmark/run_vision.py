import sys, os, re, io, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyautogui
import ollama
from PIL import ImageGrab, Image
from pywinauto import Desktop
from run_hard import (TASKS, TARGET, find_window, exists, open_page,
                      close_page, page_title, clicked_value)

VLM = os.environ.get("VH_VLM", "qwen2.5vl:7b")
TAG = os.environ.get("VH_TAG", "dev")
IN_W = 1176        # input width that gave exact coordinates in the checks
TOP_FRAC = 0.17    # safety: never click in the browser toolbar area

def ask_target(img, goal):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    prompt = (f'The goal is: "{goal}". This is a screenshot of a web page. '
              "Find the single element that should be clicked to achieve the goal, "
              "and output its bounding box in JSON format, like "
              '[{"bbox_2d": [x1, y1, x2, y2], "label": "what it is"}].')
    out = ollama.chat(model=VLM, options={"temperature": 0},
                      messages=[{"role": "user", "content": prompt,
                                 "images": [buf.getvalue()]}])
    text = out["message"]["content"]
    for chunk in re.findall(r"\{[^{}]*\}", text):
        try:
            box = [float(v) for v in json.loads(chunk).get("bbox_2d")]
        except Exception:
            continue
        if len(box) == 4:
            return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, text
    return None, None, text

def vision_click(goal):
    win = find_window()
    win.set_focus()
    time.sleep(0.8)
    r = win.rectangle()
    sw, sh = pyautogui.size()
    left, top = max(r.left, 0), max(r.top, 0)
    right, bottom = min(r.right, sw), min(r.bottom, sh)
    shot = ImageGrab.grab(bbox=(left, top, right, bottom)).convert("RGB")
    w0, h0 = shot.size
    H = max(28, round(h0 * IN_W / w0 / 28) * 28)
    img = shot.resize((IN_W, H), Image.LANCZOS)

    x, y, raw = ask_target(img, goal)
    print("Model answer:", raw.replace("\n", " ")[:200])
    if x is None:
        return False, "no-answer"
    if not (0 <= x <= IN_W and TOP_FRAC * H <= y <= H):
        return False, f"refused:({x:.0f},{y:.0f}) outside the page area"
    active = Desktop(backend="uia").window(active_only=True).window_text()
    if not re.match(TARGET, active):
        return False, f"wrong-window:{active}"
    rx, ry = left + x * w0 / IN_W, top + y * h0 / H
    pyautogui.click(int(rx), int(ry))
    time.sleep(1.0)
    return True, f"click:({rx:.0f},{ry:.0f})"

if __name__ == "__main__":
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    only = sys.argv[2:]
    print("Vision model:", VLM, "| Tag:", TAG, "| mode: screenshot-only | page: hard")
    if exists():
        print("A 'VH Hard Page' window is already open. Close it and run again.")
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
                    finished, action = vision_click(task["goal"])
                except pyautogui.FailSafeException:
                    print("FAILSAFE: stopped by mouse in screen corner")
                    raise
                except Exception as e:
                    finished, action = False, f"error:{e}"
                    print("ERROR:", e)
                secs = round(time.time() - t0, 1)
                got = clicked_value(page_title())
                ok = got == task["expect"]
                rec = {"tag": TAG, "mode": "vision", "page": "hard", "model": VLM,
                       "task": task["id"], "trial": trial, "finished": finished,
                       "success": ok, "expected": task["expect"],
                       "got": got if got is not None else "(nothing clicked)",
                       "seconds": secs, "actions": [action]}
                print("RESULT:", rec)
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                close_page()
    print("BENCHMARK COMPLETE")