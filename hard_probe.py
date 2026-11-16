import os, time, subprocess
from pywinauto import Desktop
from observe import observe

PAGE_DIR = os.path.abspath("benchmark/pages")
PAGE = os.path.join(PAGE_DIR, "hard.html")
TITLE_RE = r"VH Hard Page.*Edge"

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>VH Hard Page</title>
<style>
  body { font-family: sans-serif; padding: 40px; }
  .row { display: flex; gap: 24px; margin: 24px 0; }
  .sq { width: 110px; height: 110px; border-radius: 12px; cursor: pointer; }
  canvas { border: 2px solid #888; cursor: pointer; }
</style>
</head>
<body>
<h1>VoiceHands hard page</h1>
<p>Squares and a canvas. None of them has a text label.</p>
<div class="row">
  <div class="sq" style="background:#e53935" onclick="hit('red')"></div>
  <div class="sq" style="background:#43a047" onclick="hit('green')"></div>
  <div class="sq" style="background:#1e88e5" onclick="hit('blue')"></div>
</div>
<canvas id="c" width="360" height="160" onclick="hit('canvas')"></canvas>
<script>
function hit(what) { document.title = 'CLICKED:' + what; }
var ctx = document.getElementById('c').getContext('2d');
ctx.fillStyle = '#fdd835';
ctx.beginPath(); ctx.arc(180, 80, 60, 0, 6.283); ctx.fill();
</script>
</body>
</html>
"""

def main():
    os.makedirs(PAGE_DIR, exist_ok=True)
    with open(PAGE, "w", encoding="utf-8") as f:
        f.write(HTML)
    url = "file:///" + PAGE.replace("\\", "/")
    subprocess.Popen(["cmd", "/c", "start", "", "msedge", "--new-window", url])
    print("Opening the hard page in a new Edge window...")
    time.sleep(7)
    try:
        win = Desktop(backend="uia").window(title_re=TITLE_RE, found_index=0)
        win.set_focus()
        time.sleep(0.6)
    except Exception as e:
        print("Could not find the hard page window:", e)
        return

    total = named = 0
    unnamed_types = {}
    for el in win.descendants():
        try:
            if not el.is_visible():
                continue
            info = el.element_info
            total += 1
            if info.name:
                named += 1
            else:
                t = str(info.control_type)
                unnamed_types[t] = unnamed_types.get(t, 0) + 1
        except Exception:
            continue

    items = observe(max_items=400, title_re=TITLE_RE)
    lines = [f"{len(items)} elements the observer can use"]
    lines += [f'{it["id"]} {it["role"]} | {it["name"]}' for it in items]
    with open("logs/observe_edge_hard.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Visible elements in total: {total}")
    print(f"  with a name (the observer keeps these): {named}")
    print(f"  without a name (the observer drops these): {total - named}")
    print("  unnamed by type:", unnamed_types)
    names = " ".join(it["name"] for it in items)
    for want in ("VoiceHands hard page", "Squares and a canvas"):
        print(f"{want!r} visible to the observer:", want in names)
    print("Saved the observer's view to logs/observe_edge_hard.txt")

if __name__ == "__main__":
    main()