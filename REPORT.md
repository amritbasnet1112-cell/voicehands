# VoiceHands: Evaluating Local Hybrid GUI Grounding and Bilingual Voice Control on Windows

**Author:** Amrit Basnet  
**Stack:** Python 3.12 · Windows UI Automation (`pywinauto`) · `faster-whisper` (`small`, int8 CPU) · Ollama (`qwen2.5:3b`, `qwen2.5:7b`, `qwen2.5vl:7b`)

## 1. Abstract

Local desktop agents face two core bottlenecks: accessibility trees miss unlabeled or ambiguous web controls, while pure vision-language grounding is slow on consumer CPUs. **VoiceHands** is a fully local, English/Japanese voice-controlled Windows agent combining a structured LLM planner, a `hybrid-safe` grounding layer (UIA tree with ambiguity-aware vision fallback), and a bilingual spoken safety gate. Across 12 benchmark series logged reproducibly in JSONL, `hybrid-safe` matches vision-only accuracy (100%) on mixed and duplicate-label pages while cutting latency on uniquely labeled elements; inside the end-to-end planner loop, `qwen2.5:7b` achieves 100% task accuracy and 83% clean termination on both development (`mp3`) and held-out unseen (`unseen1`) pages, compared to 0% clean termination on `qwen2.5:3b`. Constraining Whisper language detection to `en`/`ja` with language-separated generic hints eliminates cross-script bleed and achieves 100% language detection (0.0% EN WER, 7.4% JA CER) on unseen bilingual commands.

## 2. System Architecture

```text
[Microphone] -> faster-whisper (EN/JA constrained, split generic hints)
                     |
                     v
[Observe: UIA Tree] -> [LLM Planner (qwen2.5:7b, JSON actions + history)]
                                |
          +---------------------+---------------------+
          |                                           |
   [Risky action?]                          [Safe action / done]
          |                                           |
   [Spoken Safety Gate]                     +---------+---------+
   (EN/JA yes -> proceed,                   |                   |
    default -> cancel)               [UIA click/type]    [click_desc -> hybrid-safe]
                                                         (1 UIA match -> UIA click;
                                                          0 or >1 match -> qwen2.5vl:7b)
```

1. **Observe & Plan (`observe.py`, `planner.py`, `main.py`):** Captures visible UIA elements and asks a local Ollama model for the next structured JSON action (`click`, `click_desc`, `type`, `hotkey`, `done`) with an action history and a 4-step loop guard.
2. **Ambiguity-Aware Grounding (`ground.py`):** Executes direct UIA clicks when a unique accessible target exists, and falls back to `qwen2.5vl:7b` (1176 px input width) when an element is unlabeled or when multiple controls share the same label (`hybrid-safe`).
3. **Bilingual Voice & Safety Gate (`voice.py`, `voice_main.py`):** Restricts `faster-whisper` language detection to `("en", "ja")`, applies language-matched generic domain hints, and intercepts `risky=True` actions for spoken confirmation (`yes`/`はい`), failing closed on unclear audio.

## 3. Experimental Methodology

All benchmarks run end-to-end on a single Windows 11 laptop against real Notepad windows and local Microsoft Edge test pages, verified programmatically (reading back Notepad text or reading `CLICKED:<id>` from the browser tab title). Every run is appended to `logs/benchmark.jsonl` or `logs/asr_bench.jsonl` and aggregated by `benchmark/results_table.py`. To test against overfitting, key fixes are evaluated on held-out unseen fixtures (`dp2` for duplicate labels, `mixed2`/`unseen1` for the planner loop, and `asr3` for bilingual ASR) with zero prompt modifications.

## 4. Key Results

### 4.1 Grounding Ablation (UIA vs. Vision vs. Hybrid-Safe)
* **Unlabeled elements (`hu1` vs. `hv1`):** UIA-only failed completely (**0/8** for both `3b` and `7b`), whereas `qwen2.5vl:7b` achieved **4/4** (median 11 s).
* **Mixed labeled + unlabeled (`mx1`):** `uia-rules` hit **6/12** (2 s), `vision-7b` hit **12/12** (11 s), and `hybrid` matched **12/12** at nearly half the median latency (**6 s**).
* **Duplicate labels (`dp1`–`dp3`):** Naive `hybrid` silently clicked the first matching button (**4/6** on both pages A and B). Escalating multi-match ambiguity to vision (`hybrid-safe`) achieved **6/6** on unseen page B (`dp2`) and **6/6** on page A (`dp3`).

### 4.2 End-to-End Planner Loop & Generalization (`mp1`–`mp3`, `unseen1`)
* **Prompt iteration:** Logging the clicked element name into history plus a 1-step click example (`mp3`) raised `qwen2.5:7b` from 3/6 (`mp1`) and 2/6 (`mp2` regression) to **6/6 (100%) accuracy and 5/6 (83%) clean stops** (39 s median).
* **Unseen generalization (`unseen1`):** On `mixed2.html` (new button names, circles instead of squares, flipped layout, untouched prompt), `qwen2.5:7b` replicated **6/6 (100%) accuracy and 5/6 (83%) clean stops** (38 s median).
* **Model-size scaling:** Across all 12 dev + unseen tasks, `qwen2.5:3b` achieved **12/12** output accuracy but **0/12** clean stops, relying entirely on the loop guard.

### 4.3 Bilingual ASR (`asr1`–`asr3`)
* **Baseline (`asr1`, `medium`, 99-lang + mixed prompt):** EN lang accuracy **2/5**, **50.0% WER**; JA lang accuracy **4/5**, **8.9% CER** (~37 s/utterance).
* **Constrained + leak-free unseen test (`asr3`, `small`, EN/JA only + generic hints):** **3/3 (100%)** EN lang accuracy with **0.0% WER** (11.8 s avg) and **3/3 (100%)** JA lang accuracy with **7.4% CER** (24.4 s avg).

## 5. Failure Taxonomy

| Failure Mode | Where Observed | Root Cause | Mitigation |
|---|---|---|---|
| **UIA Blindness** | `hu1` (0/8) | Unlabeled `<div>` targets absent from UIA tree | Vision fallback (`click_desc`) |
| **Silent Duplicate Click** | `dp1`, `dp2` (4/6) | Naive UIA name match picked first DOM match | `hybrid-safe` escalates `>1` match to vision |
| **Loop Non-Termination** | `v5`, `mp1`–`mp3`, `unseen1` (`3b`: 0% fin) | Small planner repeats last action without `done` | 7B planner + element-name history + loop guard |
| **Prompt Regression** | `mp2` (3b: 3/6, 7b: 5/6) | Generic done rule without specific target feedback | Reverted & replaced with explicit element feedback (`mp3`) |
| **Cross-Script ASR Bleed** | `asr1` (50% EN WER) | Mixed EN/JA `initial_prompt` + 99-lang auto-detect | EN/JA constrained detection + split generic hints |
| **Homophone Substitution** | `asr3` (`uja2`: `詳細`→`消災`) | Acoustically identical kanji in short command | Fuzzy/phonetic matching in downstream UIA lookup (future work) |

## 6. Limitations & Future Work

Current results come from a single Windows 11 laptop, a single speaker, and synthetic local test pages (3–8 tasks per suite). Next steps are: (1) multi-step workflows across real web apps, (2) Nepali ASR evaluation, and (3) GPU-accelerated inference to bring vision and ASR latency under 2 seconds per step.