import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice import listen_with_lang
from benchmark.run_asr import error_rate

PROMPTS = [
    {"id": "uen1", "lang": "en", "ref": "Click the Filter button"},
    {"id": "uen2", "lang": "en", "ref": "Click the orange circle"},
    {"id": "uen3", "lang": "en", "ref": "Open the settings menu"},
    {"id": "uja1", "lang": "ja", "ref": "青い丸をクリックして"},
    {"id": "uja2", "lang": "ja", "ref": "詳細ボタンを押して"},
    {"id": "uja3", "lang": "ja", "ref": "はい、お願いします"},
]

if __name__ == "__main__":
    tag = os.environ.get("VH_TAG", "asr3")
    rows = []
    print(f"VoiceHands Unseen ASR Benchmark (tag: {tag}) — 6 prompts (3 EN, 3 JA)")
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

    print("\n=== UNSEEN ASR SUMMARY ===")
    for lang, metric in [("en", "WER"), ("ja", "CER")]:
        sub = [r for r in rows if r["lang"] == lang]
        lang_ok = sum(r["lang_ok"] for r in sub)
        avg_er = sum(r["error_rate"] for r in sub) / len(sub)
        avg_s = sum(r["seconds"] for r in sub) / len(sub)
        print(f"  {lang.upper()}: lang_acc={lang_ok}/{len(sub)} | avg {metric}={avg_er*100:.1f}% | avg sec={avg_s:.1f}s")