import json, sys
from collections import defaultdict

# Tags hidden from the default report, with the reason.
EXCLUDED = {
    "v0": "legacy: early runs, mixed code versions and element limits",
    "v1": "invalid: ran in a real Notepad tab, not a scratch file",
    "v3": "invalid: scratch-tab focus bug made setup and readback unreliable",
}

arg = sys.argv[1] if len(sys.argv) > 1 else None
rows = [json.loads(l) for l in open("logs/benchmark.jsonl", encoding="utf-8")]
for r in rows:
    r.setdefault("model", "qwen2.5:7b")
    r.setdefault("tag", "v0")

if arg == "all":
    pass
elif arg:
    rows = [r for r in rows if r["tag"] == arg]
else:
    rows = [r for r in rows if r["tag"] not in EXCLUDED]

groups = defaultdict(list)
for r in rows:
    groups[(r["tag"], r["model"])].append(r)
keys = sorted(groups)

summary = []
summary.append(f"{'tag':<6}{'model':<14}{'runs':<6}{'success':<14}{'finished':<14}{'avg sec':<8}")
for (tag, m) in keys:
    rs = groups[(tag, m)]
    n = len(rs)
    ok = sum(r["success"] for r in rs)
    fin = sum(r["finished"] for r in rs)
    avg = sum(r["seconds"] for r in rs) / n
    summary.append(f"{tag:<6}{m:<14}{n:<6}{f'{ok}/{n} ({100*ok/n:.0f}%)':<14}"
                   f"{f'{fin}/{n} ({100*fin/n:.0f}%)':<14}{avg:<8.0f}")

summary.append("")
summary.append("TASK MATRIX (output correct / stopped cleanly)")
summary.append(f"{'task':<6}" + "".join(f"{t + ' ' + m.split(':')[-1]:<18}" for t, m in keys))
for task in sorted({r["task"] for r in rows}):
    cells = []
    for k in keys:
        rs = [r for r in groups[k] if r["task"] == task]
        if rs:
            ok = sum(r["success"] for r in rs)
            fin = sum(r["finished"] for r in rs)
            cells.append(f"{ok}/{len(rs)} ok {fin}/{len(rs)} fin")
        else:
            cells.append("-")
    summary.append(f"{task:<6}" + "".join(f"{c:<18}" for c in cells))

lines = list(summary)

problems = [r for r in rows if not r["success"] or not r["finished"]]
if problems:
    lines.append("")
    lines.append("PROBLEM RUNS:")
    for r in problems:
        kind = "wrong output" if not r["success"] else "output OK but did not stop cleanly"
        lines.append(f"  [{r['tag']}] {r['model']} {r['task']}: {kind} "
                     f"(expected={r['expected']!r} got={r['got']!r})")
        if r.get("actions"):
            lines.append("      actions: " + " > ".join(r["actions"]))

if not arg:
    lines.append("")
    lines.append("Hidden tags: " + "; ".join(f"{t} ({why})" for t, why in EXCLUDED.items()))

text = "\n".join(lines)
with open("logs/report.txt", "w", encoding="utf-8") as f:
    f.write(text)

print(text)
print("\n=== SUMMARY (repeated so it stays visible) ===")
print("\n".join(summary))