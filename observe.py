from pywinauto import Desktop
import json, time, sys, os

CHROME_FRAC = 0.17   # top part of an Edge window: tabs, address bar, bookmarks, extensions

def observe(max_items=None, title_re=None):
    if max_items is None:
        max_items = int(os.environ.get("VH_MAX_ITEMS", "25"))
    if title_re:
        win = Desktop(backend="uia").window(title_re=title_re, found_index=0)
        win.set_focus()
        time.sleep(0.6)
    else:
        win = Desktop(backend="uia").window(active_only=True)

    wr = win.rectangle()
    is_browser = win.window_text().rstrip().endswith("Edge")
    limit = wr.top + CHROME_FRAC * (wr.bottom - wr.top) if is_browser else None

    items = []
    for i, el in enumerate(win.descendants()):
        try:
            info = el.element_info
            if (info.name or info.control_type in ("Edit", "Document")) and el.is_visible():
                r = el.rectangle()
                if limit is not None and (r.top + r.bottom) / 2 < limit:
                    continue   # browser toolbar, address bar, bookmarks, extensions
                items.append({
                    "id": i,
                    "role": info.control_type,
                    "name": info.name or "(text area)",
                    "box": [r.left, r.top, r.right, r.bottom],
                })
        except Exception:
            continue
    return items[:max_items]

if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "test"
    print(f"Click the target window now. Reading in 8 seconds... (tag: {tag})")
    time.sleep(8)
    win = Desktop(backend="uia").window(active_only=True)
    title = win.window_text()
    items = observe(max_items=300)
    lines = [f"WINDOW: {title}", f"{len(items)} elements"]
    lines += [f'{it["id"]} {it["role"]} | {it["name"]}' for it in items]
    with open(f"logs/observe_{tag}.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"WINDOW: {title}")
    print(f"{len(items)} elements -> saved to logs/observe_{tag}.txt")