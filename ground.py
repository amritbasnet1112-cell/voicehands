import os, re, io, json, time
import pyautogui
import ollama
from PIL import ImageGrab, Image
from pywinauto import Desktop

VLM = os.environ.get("VH_VLM", "qwen2.5vl:7b")
IN_W = 1176        # vision input width that gave exact coordinates in my checks
TOP_FRAC = 0.17    # never click in the browser toolbar area
CLICKABLE = ("Button", "Hyperlink", "MenuItem", "CheckBox", "RadioButton",
             "TabItem", "ListItem", "Edit")

def _window(title_re):
    if title_re:
        return Desktop(backend="uia").window(title_re=title_re, found_index=0)
    return Desktop(backend="uia").window(active_only=True)

def _box(win):
    r = win.rectangle()
    sw, sh = pyautogui.size()
    return max(r.left, 0), max(r.top, 0), min(r.right, sw), min(r.bottom, sh)

def _active_ok(title_re):
    if not title_re:
        return True
    try:
        t = Desktop(backend="uia").window(active_only=True).window_text()
    except Exception:
        return False
    return re.match(title_re, t) is not None

def _uia_match(win, desc, box):
    """Clickable elements whose accessible name appears in the description.
    Returns (name, cx, cy, n) for the longest matching name; n = how many elements share it."""
    left, top, right, bottom = box
    limit = top + TOP_FRAC * (bottom - top)
    d = desc.lower()
    found = []
    for el in win.descendants():
        try:
            if not el.is_visible():
                continue
            info = el.element_info
            name = (info.name or "").strip()
            if len(name) < 3 or name.lower() not in d:
                continue
            if str(info.control_type) not in CLICKABLE:
                continue
            r = el.rectangle()
            cx, cy = (r.left + r.right) // 2, (r.top + r.bottom) // 2
            if left <= cx <= right and limit <= cy <= bottom:
                found.append((name, cx, cy))
        except Exception:
            continue
    if not found:
        return None
    best = max(found, key=lambda f: len(f[0]))
    n = sum(1 for f in found if f[0].lower() == best[0].lower())
    return best[0], best[1], best[2], n

def _vision_point(img, desc):
    goal = desc if desc.lower().startswith("click") else "Click " + desc
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

def click(title_re, desc):
    """Hybrid-safe click. Returns (ok, note)."""
    win = _window(title_re)
    win.set_focus()
    time.sleep(0.8)
    box = _box(win)

    hit = _uia_match(win, desc, box)
    note = ""
    if hit and hit[3] == 1:
        name, cx, cy, _ = hit
        if not _active_ok(title_re):
            return False, "uia:wrong-window"
        pyautogui.click(cx, cy)
        time.sleep(1.0)
        return True, f"uia:{name}@({cx},{cy})"
    if hit:
        note = f"ambiguous:{hit[0]}x{hit[3]}->"

    left, top, right, bottom = box
    shot = ImageGrab.grab(bbox=box).convert("RGB")
    w0, h0 = shot.size
    H = max(28, round(h0 * IN_W / w0 / 28) * 28)
    img = shot.resize((IN_W, H), Image.LANCZOS)
    x, y, raw = _vision_point(img, desc)
    print("   vision answer:", raw.replace("\n", " ")[:160])
    if x is None:
        return False, note + "vision:no-answer"
    if not (0 <= x <= IN_W and TOP_FRAC * H <= y <= H):
        return False, note + f"vision:refused ({x:.0f},{y:.0f})"
    if not _active_ok(title_re):
        return False, note + "vision:wrong-window"
    rx, ry = left + x * w0 / IN_W, top + y * h0 / H
    pyautogui.click(int(rx), int(ry))
    time.sleep(1.0)
    return True, note + f"vision:click({rx:.0f},{ry:.0f})"