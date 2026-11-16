import time
import pyautogui
import pyperclip

pyautogui.FAILSAFE = True   # move mouse to a screen corner to stop everything
pyautogui.PAUSE = 0.3

def act(action, items):
    t = action["action"]
    if t == "click":
        el = next(x for x in items if x["id"] == action["id"])
        l, top, r, b = el["box"]
        pyautogui.click((l + r) // 2, (top + b) // 2)
    elif t == "type":
        pyperclip.copy(action["text"])
        pyautogui.hotkey("ctrl", "v")
    elif t == "hotkey":
        pyautogui.hotkey(*action["keys"])
    elif t == "press":
        pyautogui.press(action["keys"][0])
    elif t == "scroll":
        pyautogui.scroll(action.get("amount", -500))
    time.sleep(0.5)