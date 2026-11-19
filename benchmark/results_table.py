import json, statistics as st
from collections import defaultdict

EXPERIMENTS = [
    ("v5",      "Notepad, 8 typing tasks, LLM planner on the UIA tree"),
    ("bu1",     "Edge form page, 3 tasks, LLM planner on the UIA tree"),
    ("hu1",     "Edge page with unlabeled shapes, 4 tasks, LLM planner on the UIA tree"),
    ("hv1",     "Same unlabeled page, screenshot-only (vision model)"),
    ("mx1",     "Edge page, 3 labeled buttons + 3 unlabeled squares, grounding modes"),
    ("dp1",     "Duplicate-label page A, grounding modes"),
    ("dp2",     "Duplicate-label page B (unseen), grounding modes"),
    ("dp3",     "Page A re-run with hybrid-safe (fix was designed on this page)"),
    ("mp1",     "Mixed page (dev), end-to-end planner loop + hybrid-safe"),
    ("mp2",     "Mixed page (dev), uniform action feedback + done rule (regressed)"),
    ("mp3",     "Mixed page (dev), element name in history + 1-step click example"),
    ("unseen1", "Unseen mixed2 page (new labels, circles, flipped layout), no prompt change"),
]

rows = [json.loads(l) for l in open("logs/benchmark.jsonl", encoding="utf-8")]
out = [
    "| Experiment | Tag | Model or mode | Tasks | Runs | Correct | Clean stop | Median s |",
    "|---|---|---|---|---|---|---|---|",
]
for tag, desc in EXPERIMENTS:
    groups = defaultdict(list)
    for r in rows:
        if r.get("tag") == tag:
            groups[r.get("model", "qwen2.5:7b")].append(r)
    first = True
    for model, rs in sorted(groups.items()):
        ok = sum(bool(r["success"]) for r in rs)
        tasks = len({r["task"] for r in rs})
        med = st.median(r["seconds"] for r in rs)
        if any("finished" in r for r in rs):
            fin = sum(bool(r.get("finished")) for r in rs)
            fin_str = f"{fin}/{len(rs)}"
        else:
            fin_str = "—"
        label = desc if first else ""
        first = False
        out.append(f"| {label} | {tag} | {model} | {tasks} | {len(rs)} | {ok}/{len(rs)} | {fin_str} | {med:.0f} |")

text = "\n".join(out)
print(text)
with open("logs/results.md", "w", encoding="utf-8") as f:
    f.write(text)