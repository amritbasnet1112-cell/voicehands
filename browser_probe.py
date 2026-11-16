import os, time, subprocess
from observe import observe

PAGE_DIR = os.path.abspath("benchmark/pages")
PAGE = os.path.join(PAGE_DIR, "form.html")

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>VH Test Page</title>
<style>
  body { font-family: sans-serif; padding: 40px; }
  input, button { font-size: 20px; padding: 8px; margin: 8px 0; }
</style>
</head>
<body>
<h1>VoiceHands test form</h1>
<label for="name">Your name</label><br>
<input id="name" type="text" placeholder="Type your name here"><br>
<button id="go" onclick="submitForm()">Submit</button>
<p id="out"></p>
<script>
function submitForm() {
  var v = document.getElementById('name').value;
  document.getElementById('out').textContent = 'Hello ' + v;
  document.title = 'SUBMITTED:' + v;
}
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
    print("Opening the test page in a new Edge window...")
    time.sleep(7)
    try:
        items = observe(max_items=400, title_re=r"VH Test Page.*Edge")
    except Exception as e:
        print("Could not find the test window:", e)
        return
    lines = [f"{len(items)} elements"]
    lines += [f'{it["id"]} {it["role"]} | {it["name"]}' for it in items]
    with open("logs/observe_edge.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(len(items), "elements -> saved to logs/observe_edge.txt")
    names = " ".join(it["name"] for it in items)
    for want in ("VoiceHands test form", "Your name", "Submit"):
        print(f"{want!r} visible to the observer:", want in names)

if __name__ == "__main__":
    main()