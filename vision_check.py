import sys, os, re, json, time
import numpy as np
from PIL import Image

IMG = "logs/vision_in.png"
VLM = os.environ.get("VH_VLM", "qwen2.5vl:7b")

COLORS = {
    "red": (229, 57, 53),
    "green": (67, 160, 71),
    "blue": (30, 136, 229),
    "yellow_circle": (253, 216, 53),
}

# The first probe's answers, copied from its terminal output.
OLD = {"red": (99, 310), "green": (210, 310), "blue": (330, 310), "yellow_circle": (200, 460)}

def find_truth(img):
    a = np.asarray(img.convert("RGB")).astype(int)
    top = int(a.shape[0] * 0.2)   # skip the browser toolbar and bookmarks bar
    page = a[top:]
    out = {}
    for name, c in COLORS.items():
        d = np.abs(page - np.array(c)).sum(axis=2)
        ys, xs = np.where(d < 45)
        if len(xs) < 50:
            out[name] = None
            continue
        out[name] = {"cx": xs.mean(), "cy": ys.mean() + top,
                     "box": (xs.min(), ys.min() + top, xs.max(), ys.max() + top)}
    return out

def report(title, answers, truth):
    print(f"\n=== {title} ===")
    print(f"{'shape':<15}{'truth':<14}{'model':<14}{'error':<14}inside the shape?")
    tx, mx, ty, my = [], [], [], []
    hits = 0
    for name in COLORS:
        t, m = truth.get(name), answers.get(name)
        if t is None:
            print(f"{name:<15}not found in the screenshot")
            continue
        s_true = "(%.0f,%.0f)" % (t["cx"], t["cy"])
        if m is None:
            print(f"{name:<15}{s_true:<14}no answer")
            continue
        x0, y0, x1, y1 = t["box"]
        inside = x0 <= m[0] <= x1 and y0 <= m[1] <= y1
        hits += inside
        s_model = "(%.0f,%.0f)" % (m[0], m[1])
        s_err = "(%+.0f,%+.0f)" % (m[0] - t["cx"], m[1] - t["cy"])
        print(f"{name:<15}{s_true:<14}{s_model:<14}{s_err:<14}{inside}")
        tx.append(t["cx"]); mx.append(m[0]); ty.append(t["cy"]); my.append(m[1])
    print(f"inside the right shape: {hits}/{len(COLORS)}")
    if len(tx) >= 3:
        ax, bx = np.polyfit(tx, mx, 1)
        ay, by = np.polyfit(ty, my, 1)
        print("fit: model_x = %.2f * true_x %+.0f | model_y = %.2f * true_y %+.0f" % (ax, bx, ay, by))

def ask():
    import ollama
    prompt = ("Locate the red square, the green square, the blue square and the yellow circle "
              "in this image. Output the bounding box of each one in JSON format, like "
              '[{"bbox_2d": [x1, y1, x2, y2], "label": "red square"}].')
    with open(IMG, "rb") as f:
        data = f.read()
    print(f"Asking {VLM}. This can take several minutes on a laptop CPU...")
    t0 = time.time()
    out = ollama.chat(model=VLM, options={"temperature": 0},
                      messages=[{"role": "user", "content": prompt, "images": [data]}])
    print(f"Model call took {time.time() - t0:.0f} s")
    text = out["message"]["content"]
    print("Raw answer:", text)
    answers = {}
    for chunk in re.findall(r"\{[^{}]*\}", text):
        try:
            obj = json.loads(chunk)
            box = [float(v) for v in obj.get("bbox_2d")]
            label = str(obj.get("label", "")).lower()
        except Exception:
            continue
        if len(box) != 4:
            continue
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        for name in COLORS:
            if name.split("_")[0] in label or (name == "yellow_circle" and "circle" in label):
                answers[name] = (cx, cy)
    return answers

if __name__ == "__main__":
    img = Image.open(IMG)
    print("Image size:", img.size)
    truth = find_truth(img)
    report("FIRST PROBE (centre-point prompt)", OLD, truth)
    if "--ask" in sys.argv:
        report("BOUNDING-BOX PROMPT", ask(), truth)