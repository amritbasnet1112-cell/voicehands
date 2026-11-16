import json
import os
import ollama

PLANNER = os.environ.get("VH_MODEL", "qwen2.5:7b")

SYSTEM = """You control a Windows PC. You get a goal, a numbered list of UI elements,
the actions already taken, and a hint. Reply with ONE JSON object only:
{"action":"click|type|hotkey|press|scroll|done","id":int,"text":str,"keys":[str],"risky":bool}

Rules:
- click needs "id" from the list. type needs "text".
- hotkey needs "keys" with a combination, e.g. ["ctrl","a"].
- press needs "keys" with exactly ONE key, e.g. ["enter"] or ["delete"].
- Typing goes into the focused element, so click the text area first, then type.
- Set risky=true only for deleting files, sending messages, purchases, or submitting forms. Editing text is not risky.
- Never click Close, Minimize, Maximize, or tabs. The typing area is named "(text area)".
- Each reply must be the NEXT step. Never repeat the last action.
- When every step of the goal has been done, reply {"action":"done"}.

Example for the goal "Click the text area and type hi":
Actions so far: []  -> {"action":"click","id":1,"text":"","keys":[],"risky":false}
Actions so far: [click id 1]  -> {"action":"type","id":1,"text":"hi","keys":[],"risky":false}
Actions so far: [click id 1, type "hi"]  -> {"action":"done"}

Example for the goal "Click the text area, press the end key, then type ok":
Actions so far: []  -> {"action":"click","id":1,"text":"","keys":[],"risky":false}
Actions so far: [click id 1]  -> {"action":"press","id":1,"text":"","keys":["end"],"risky":false}
Actions so far: [click id 1, press end]  -> {"action":"type","id":1,"text":"ok","keys":[],"risky":false}
Actions so far: [click id 1, press end, type "ok"]  -> {"action":"done"}"""

def plan(goal, items, history):
    done = [h for h in history if "error" not in h]
    if done:
        last = done[-1]
        hint = (f"Your last successful action was {json.dumps(last, ensure_ascii=False)}. "
                "Do NOT repeat it. Choose the next step, or done if the goal is complete.")
    else:
        hint = "No actions taken yet. Choose the first step."
    msg = (f"Goal: {goal}\n"
           f"Actions so far: {json.dumps(history[-6:], ensure_ascii=False)}\n"
           f"Hint: {hint}\n"
           f"Elements: {json.dumps(items, ensure_ascii=False)}")
    out = ollama.chat(
        model=PLANNER, format="json",
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": msg}],
        options={"temperature": 0},
    )
    return json.loads(out["message"]["content"])