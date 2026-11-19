import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VH_MAX_ITEMS", "80")

import pyautogui
import run_mixed as rm
from run_hard import log_len, actions_since
from main import run

MODEL = os.environ.get("VH_MODEL", "qwen2.5:7b")

if __name__ == "__main__":
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    only = sys.argv[2:]
    print("Model:", MODEL, "| Tag:", rm.TAG, "| planner loop | page: mixed")
    if rm.exists():
        print("A 'VH Mixed Page' window is already open. Close it and run again.")
        sys.exit(1)
    with open("logs/benchmark.jsonl", "a", encoding="utf-8") as out:
        for task in rm.TASKS:
            if only and task["id"] not in only:
                continue
            for trial in range(trials):
                rm.open_page()
                if not rm.exists():
                    print("SKIPPED (test page did not open):", task["id"])
                    continue
                start = log_len()
                t0 = time.time()
                try:
                    finished = run(task["goal"], rm.TARGET)
                except pyautogui.FailSafeException:
                    print("FAILSAFE: stopped by mouse in screen corner")
                    raise
                except Exception as e:
                    finished = False
                    print("ERROR:", e)
                secs = round(time.time() - t0, 1)
                got = rm.clicked_value(rm.page_title())
                rec = {"tag": rm.TAG, "mode": "loop", "page": "mixed",
                       "model": MODEL, "task": task["id"], "trial": trial,
                       "finished": finished, "success": got == task["expect"],
                       "expected": task["expect"],
                       "got": got if got is not None else "(nothing clicked)",
                       "seconds": secs, "actions": actions_since(start)}
                print("RESULT:", rec)
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                rm.close_page()
    print("BENCHMARK COMPLETE")