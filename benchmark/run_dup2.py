import sys, os, json, time
import pyautogui
import run_mixed as rm

rm.TARGET = r"(VH Dup [AB]|CLICKED).*Edge"
LABELS = dict(rm.LABELS)
LABELS["safe"] = "hybrid-safe"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>@@TITLE@@</title>
<style>
  body { margin: 0; font-family: sans-serif; }
  button { position: absolute; width: 150px; height: 60px; font-size: 22px; }
</style>
</head>
<body>
<h1 style="position:absolute; left:60px; top:30px">@@TITLE@@</h1>
@@BUTTONS@@<script>function hit(w) { document.title = 'CLICKED:' + w; }</script>
</body>
</html>
"""

def page_html(title, buttons):
    items = ""
    for x, y, text, val in buttons:
        items += '<button style="left:%dpx; top:%dpx" onclick="hit(\'%s\')">%s</button>\n' % (x, y, val, text)
    return TEMPLATE.replace("@@TITLE@@", title).replace("@@BUTTONS@@", items)

VARIANTS = {
    "a": {"title": "VH Dup A", "file": "dup_a.html",
          "buttons": [(120, 260, "Save", "save-left"), (700, 260, "Save", "save-right"),
                      (410, 420, "Cancel", "cancel")],
          "tasks": [("d01", "Click the left Save button", "save-left"),
                    ("d02", "Click the right Save button", "save-right"),
                    ("d03", "Click the Cancel button", "cancel")]},
    "b": {"title": "VH Dup B", "file": "dup_b.html",
          "buttons": [(120, 230, "Open", "open-top"), (120, 470, "Open", "open-bottom"),
                      (700, 350, "Close", "close")],
          "tasks": [("e01", "Click the top Open button", "open-top"),
                    ("e02", "Click the bottom Open button", "open-bottom"),
                    ("e03", "Click the Close button", "close")]},
}

def uia_resolve_counted(win, goal, box):
    """Like the rule-based lookup, but also counts how many elements share the matched name."""
    left, top, right, bottom = box
    limit = top + rm.TOP_FRAC * (bottom - top)
    g = goal.lower()
    best, counts = None, {}
    for el in win.descendants():
        try:
            if not el.is_visible():
                continue
            info = el.element_info
            name = (info.name or "").strip()
            if len(name) < 3 or name.lower() not in g:
                continue
            if str(info.control_type) not in rm.CLICKABLE:
                continue
            r = el.rectangle()
            cx, cy = (r.left + r.right) // 2, (r.top + r.bottom) // 2
            if not (left <= cx <= right and limit <= cy <= bottom):
                continue
            counts[name.lower()] = counts.get(name.lower(), 0) + 1
            if best is None or len(name) > len(best[0]):
                best = (name, cx, cy)
        except Exception:
            continue
    n = counts.get(best[0].lower(), 0) if best else 0
    return best, n

def solve(mode, goal):
    if mode != "safe":
        return rm.solve(mode, goal)
    win = rm.find_window()
    win.set_focus()
    time.sleep(0.8)
    box = rm.window_box(win)
    hit, n = uia_resolve_counted(win, goal, box)
    note = ""
    if hit and n == 1:
        name, cx, cy = hit
        ok, active = rm.active_ok()
        if not ok:
            return False, f"uia:wrong-window {active}"
        pyautogui.click(cx, cy)
        time.sleep(1.0)
        return True, f"uia:{name}@({cx},{cy})"
    if hit:
        note = f"ambiguous:{hit[0]}x{n}->"
    ok, action = rm.vision_click(goal, box)
    return ok, note + action

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    trials = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    variant = sys.argv[3] if len(sys.argv) > 3 else "b"
    if mode not in LABELS or variant not in VARIANTS:
        print("Usage: python benchmark\\run_dup2.py <uia|vision|hybrid|safe> [trials] [a|b]")
        sys.exit(1)
    v = VARIANTS[variant]
    rm.PAGE = os.path.join(rm.PAGE_DIR, v["file"])
    rm.HTML = page_html(v["title"], v["buttons"])
    print("Mode:", mode, "| Tag:", rm.TAG, "| page: dup-" + variant)
    if rm.exists():
        print("A 'VH Dup' window is already open. Close it and run again.")
        sys.exit(1)
    with open("logs/benchmark.jsonl", "a", encoding="utf-8") as out:
        for tid, goal, expect in v["tasks"]:
            for trial in range(trials):
                rm.open_page()
                if not rm.exists():
                    print("SKIPPED (test page did not open):", tid)
                    continue
                t0 = time.time()
                try:
                    finished, action = solve(mode, goal)
                except pyautogui.FailSafeException:
                    print("FAILSAFE: stopped by mouse in screen corner")
                    raise
                except Exception as e:
                    finished, action = False, f"error:{e}"
                    print("ERROR:", e)
                secs = round(time.time() - t0, 1)
                got = rm.clicked_value(rm.page_title())
                rec = {"tag": rm.TAG, "mode": mode, "page": "dup-" + variant,
                       "model": LABELS[mode], "task": tid, "trial": trial,
                       "finished": finished, "success": got == expect,
                       "expected": expect,
                       "got": got if got is not None else "(nothing clicked)",
                       "seconds": secs, "actions": [action]}
                print("RESULT:", rec)
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                rm.close_page()
    print("BENCHMARK COMPLETE")