import json, sys, re, os
import pyautogui
from pywinauto import Desktop
from observe import observe
from planner import plan
from act import act

AUTO = os.environ.get("VH_AUTO") == "1"   # benchmark mode: auto-approve risky actions

def active_title():
    try:
        return Desktop(backend="uia").window(active_only=True).window_text()
    except Exception:
        return ""

def run(goal, title_re, max_steps=8):
    history = []
    recent = []
    log = open("logs/run.jsonl", "a", encoding="utf-8")
    for step in range(max_steps):
        items = observe(title_re=title_re)
        a = plan(goal, items, history)
        print(step, a)
        log.write(json.dumps({"goal": goal, "step": step, "n_items": len(items),
                              "action": a}, ensure_ascii=False) + "\n")
        log.flush()

        if a.get("action") == "done":
            print("DONE")
            return True

        key = json.dumps([a.get("action"), a.get("id"), a.get("text"), a.get("keys")])
        if key in recent:
            print("LOOP DETECTED: repeated a recent action, stopping")
            return False
        recent.append(key)
        recent = recent[-4:]

        if a.get("risky"):
            if AUTO:
                print("RISKY flagged (auto-approved in benchmark mode)")
            elif input("RISKY action. Proceed? (y/n) ").lower() != "y":
                print("Stopped by user")
                return False

        if title_re and not re.match(title_re, active_title()):
            print("WRONG WINDOW, skipping action:", active_title())
            history.append({"error": "wrong window focused"})
            continue

        try:
            act(a, items)
            history.append(a)
        except pyautogui.FailSafeException:
            print("FAILSAFE: stopped by mouse in screen corner")
            raise
        except Exception as e:
            history.append({"error": str(e)})

    print("Step limit reached")
    return False

if __name__ == "__main__":
    goal = sys.argv[1]
    title_re = sys.argv[2] if len(sys.argv) > 2 else None
    run(goal, title_re)