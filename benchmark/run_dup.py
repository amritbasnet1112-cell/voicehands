import sys, os, json, time
import pyautogui
import run_mixed as rm

rm.TARGET = r"(VH Dup Page|CLICKED).*Edge"
rm.PAGE = os.path.join(rm.PAGE_DIR, "dup.html")
rm.HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>VH Dup Page</title>
<style>
  body { margin: 0; font-family: sans-serif; }
  button { position: absolute; width: 150px; height: 60px; font-size: 22px; }
</style>
</head>
<body>
<h1 style="position:absolute; left:60px; top:30px">VoiceHands duplicate-label page</h1>
<button style="left:120px; top:260px" onclick="hit('save-left')">Save</button>
<button style="left:700px; top:260px" onclick="hit('save-right')">Save</button>
<button style="left:410px; top:420px" onclick="hit('cancel')">Cancel</button>
<script>function hit(w) { document.title = 'CLICKED:' + w; }</script>
</body>
</html>
"""

TASKS = [
    {"id": "d01", "goal": "Click the left Save button", "expect": "save-left"},
    {"id": "d02", "goal": "Click the right Save button", "expect": "save-right"},
    {"id": "d03", "goal": "Click the Cancel button", "expect": "cancel"},
]

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in rm.LABELS:
        print("Usage: python benchmark\\run_dup.py <uia|vision|hybrid> [trials]")
        sys.exit(1)
    trials = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    print("Mode:", mode, "| Tag:", rm.TAG, "| page: dup")
    if rm.exists():
        print("A 'VH Dup Page' window is already open. Close it and run again.")
        sys.exit(1)
    with open("logs/benchmark.jsonl", "a", encoding="utf-8") as out:
        for task in TASKS:
            for trial in range(trials):
                rm.open_page()
                if not rm.exists():
                    print("SKIPPED (test page did not open):", task["id"])
                    continue
                t0 = time.time()
                try:
                    finished, action = rm.solve(mode, task["goal"])
                except pyautogui.FailSafeException:
                    print("FAILSAFE: stopped by mouse in screen corner")
                    raise
                except Exception as e:
                    finished, action = False, f"error:{e}"
                    print("ERROR:", e)
                secs = round(time.time() - t0, 1)
                got = rm.clicked_value(rm.page_title())
                ok = got == task["expect"]
                rec = {"tag": rm.TAG, "mode": mode, "page": "dup",
                       "model": rm.LABELS[mode], "task": task["id"], "trial": trial,
                       "finished": finished, "success": ok, "expected": task["expect"],
                       "got": got if got is not None else "(nothing clicked)",
                       "seconds": secs, "actions": [action]}
                print("RESULT:", rec)
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                rm.close_page()
    print("BENCHMARK COMPLETE")