import sys, os, re, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice import listen_with_lang

PROMPTS = [
    {"id": "en1", "lang": "en", "ref": "Click the Alpha button"},
    {"id": "en2", "lang": "en", "ref": "Click the red square"},
    {"id": "en3", "lang": "en", "ref": "Click the text area and type hello world"},
    {"id": "en4", "lang": "en", "ref": "Press control S to save"},
    {"id": "en5", "lang": "en", "ref": "Yes, proceed"},
    {"id": "ja1", "lang": "ja", "ref": "テキストエリアをクリックしてこんにちはと入力して"},
    {"id": "ja2", "lang": "ja", "ref": "赤い四角をクリックして"},
    {"id": "ja3", "lang": "ja", "ref": "保存ボタンを押して"},
    {"id": "ja4", "lang": "ja", "ref": "はい、実行して"},
    {"id": "ja5", "lang": "ja", "ref": "いいえ、キャンセルして"},
]


def edit_dist(a, b):
    dp = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, dp[0] = dp[0], i
        for j, y in enumerate(b, 1):
            prev, dp[j] = dp[j], min(dp[j] + 1, dp[j - 1] + 1, prev + (x != y))
    return dp[-1]


def norm_en(s):
    return re.sub(r"[^a-z0-9\s]", "", s.lower()).split()


def norm_ja(s):
    return list(re.sub(r"[\s。、！？.,!?「」『』・]", "", s))


def error_rate(ref, hyp, lang):
    if lang == "en":
        r, h = norm_en(ref), norm_en(hyp)
    else:
        r, h = norm_ja(ref), norm_ja(hyp)
    return round(edit_dist(r, h) / max(len(r), 1), 3)


if __name__ == "__main__":
    tag = os.environ.get("VH_TAG", "asr1")
    rows = []
    print(f"VoiceHands ASR Benchmark (tag: {tag}) — 10 prompts (5 EN, 5 JA)")
    print("Read each prompt naturally after pressing Enter.\n")

    with open("logs/asr_bench.jsonl", "a", encoding="utf-8") as out:
        for p in PROMPTS:
            print(f"\n[{p['id']} | {p['lang']}] Say: {p['ref']}")
            t0 = time.time()
            hyp, det = listen_with_lang("Press Enter to START speaking...")
            secs = round(time.time() - t0, 1)
            er = error_rate(p["ref"], hyp, p["lang"])
            rec = {
                "tag": tag, "id": p["id"], "lang": p["lang"],
                "detected": det, "lang_ok": det == p["lang"],
                "ref": p["ref"], "hyp": hyp,
                "metric": "WER" if p["lang"] == "en" else "CER",
                "error_rate": er, "seconds": secs,
            }
            print(f"   -> det={det} | {rec['metric']}={er:.3f} | {secs}s")
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            rows.append(rec)

    print("\n=== ASR SUMMARY ===")
    for lang, metric in [("en", "WER"), ("ja", "CER")]:
        sub = [r for r in rows if r["lang"] == lang]
        lang_ok = sum(r["lang_ok"] for r in sub)
        avg_er = sum(r["error_rate"] for r in sub) / len(sub)
        avg_s = sum(r["seconds"] for r in sub) / len(sub)
        print(f"  {lang.upper()}: lang_acc={lang_ok}/{len(sub)} | avg {metric}={avg_er*100:.1f}% | avg sec={avg_s:.1f}s")