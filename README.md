# VoiceHands

A local, bilingual (English / Japanese) voice-controlled Windows agent, plus a reproducible benchmark comparing
three ways of grounding GUI clicks: the accessibility (UI Automation) tree, a vision model reading a screenshot,
and a hybrid of the two-integrated into an end-to-end LLM planner loop with a spoken safety gate.

Everything runs locally on one Windows laptop: `faster-whisper` (speech), Ollama (`qwen2.5:3b`, `qwen2.5:7b`, and
`qwen2.5vl:7b`), and `pywinauto` / `pyautogui` (observe and act).

For a concise, paper-style summary of the architecture, results, and failure taxonomy, see [REPORT.md](REPORT.md).

## Demo (sped up to skip local CPU inference wait)

https://github.com/user-attachments/assets/992adae4-d6d3-4eb9-999a-41129a798fab

## GUI Grounding & Planner Results

| Experiment | Tag | Model or mode | Tasks | Runs | Correct | Clean stop | Median s |
|---|---|---|---|---|---|---|---|
| Notepad, 8 typing tasks, LLM planner on the UIA tree | v5 | qwen2.5:3b | 8 | 8 | 6/8 | 0/8 | 73 |
|  | v5 | qwen2.5:7b | 8 | 8 | 8/8 | 7/8 | 175 |
| Edge form page, 3 tasks, LLM planner on the UIA tree | bu1 | qwen2.5:7b | 3 | 3 | 3/3 | 0/3 | 342 |
| Edge page with unlabeled shapes, 4 tasks, LLM planner on the UIA tree | hu1 | qwen2.5:3b | 4 | 8 | 0/8 | 0/8 | 64 |
|  | hu1 | qwen2.5:7b | 4 | 8 | 0/8 | 0/8 | 122 |
| Same unlabeled page, screenshot-only (vision model) | hv1 | qwen2.5vl:7b | 4 | 4 | 4/4 | 4/4 | 11 |
| Edge page, 3 labeled buttons + 3 unlabeled squares, grounding modes | mx1 | hybrid | 6 | 12 | 12/12 | 12/12 | 6 |
|  | mx1 | uia-rules | 6 | 12 | 6/12 | 6/12 | 2 |
|  | mx1 | vision-7b | 6 | 12 | 12/12 | 12/12 | 11 |
| Duplicate-label page A, grounding modes | dp1 | hybrid | 3 | 6 | 4/6 | 6/6 | 2 |
|  | dp1 | uia-rules | 3 | 6 | 4/6 | 6/6 | 2 |
|  | dp1 | vision-7b | 3 | 6 | 6/6 | 6/6 | 43 |
| Duplicate-label page B (unseen), grounding modes | dp2 | hybrid | 3 | 6 | 4/6 | 6/6 | 2 |
|  | dp2 | hybrid-safe | 3 | 6 | 6/6 | 6/6 | 44 |
|  | dp2 | uia-rules | 3 | 6 | 4/6 | 6/6 | 2 |
|  | dp2 | vision-7b | 3 | 6 | 6/6 | 6/6 | 11 |
| Page A re-run with hybrid-safe (fix was designed on this page) | dp3 | hybrid-safe | 3 | 6 | 6/6 | 6/6 | 42 |
| Mixed page (dev), end-to-end planner loop + hybrid-safe | mp1 | qwen2.5:3b | 6 | 6 | 6/6 | 0/6 | 36 |
|  | mp1 | qwen2.5:7b | 6 | 6 | 6/6 | 3/6 | 45 |
| Mixed page (dev), uniform action feedback + done rule (regressed) | mp2 | qwen2.5:3b | 6 | 6 | 3/6 | 0/6 | 49 |
|  | mp2 | qwen2.5:7b | 6 | 6 | 5/6 | 2/6 | 129 |
| Mixed page (dev), element name in history + 1-step click example | mp3 | qwen2.5:3b | 6 | 6 | 6/6 | 0/6 | 32 |
|  | mp3 | qwen2.5:7b | 6 | 6 | 6/6 | 5/6 | 39 |
| Unseen mixed2 page (new labels, circles, flipped layout), no prompt change | unseen1 | qwen2.5:3b | 6 | 6 | 6/6 | 0/6 | 35 |
|  | unseen1 | qwen2.5:7b | 6 | 6 | 6/6 | 5/6 | 38 |

How to read the table: `Tasks` is the number of distinct tasks, `Runs` is tasks times repeats, `Correct` counts runs whose final output matches ground truth, and `Clean stop` counts runs where the planner returned `done` instead of being stopped by the loop guard. Repeats at temperature 0 are not independent samples. Every result is checked by code, not by eye: Notepad's text is read back, and the test pages write what was clicked into their own tab title. Seconds are the median per run; they include model loading, vary on this laptop, and should not be compared across rows.

## Bilingual ASR Results (English & Japanese)

| Tag | Whisper model | Setup & split | EN Lang Acc | EN WER | JA Lang Acc | JA CER | Avg s (EN / JA) |
|---|---|---|---|---|---|---|---|
| asr1 | `medium` (int8) | Dev (5 EN, 5 JA), unrestricted 99-lang + mixed EN/JA prompt | 2/5 (40%) | 50.0% | 4/5 (80%) | 8.9% | 36.5 / 38.3 |
| asr2 | `small` (int8) | Dev (5 EN, 5 JA), EN/JA constrained + task hints | 5/5 (100%) | 2.5% | 5/5 (100%) | 0.0% | 16.6 / 13.6 |
| asr3 | `small` (int8) | **Unseen (3 EN, 3 JA), EN/JA constrained + generic hints** | **3/3 (100%)** | **0.0%** | **3/3 (100%)** | **7.4%** | **11.8 / 24.4** |

## What I found

1. **Notepad, UIA tree + LLM planner.** `qwen2.5:7b` got 8/8 outputs right and said `done` on 7 of 8 tasks. `qwen2.5:3b` got 6/8 outputs right and was about 2.4x faster (median 73 s vs 175 s), but never said `done` (0/8): it repeated its last action until a loop guard stopped it. On the Edge form page, 7B also repeated its final Submit click in all 3 tasks (only the 7B planner has results on that page).
2. **Unlabeled elements break the UIA tree.** On a page of unlabeled coloured shapes (4 tasks, run twice), the UIA-tree agent got 0/8 with both models.
3. **Vision can find them.** `qwen2.5vl:7b` clicked all 4 shapes correctly. Its coordinates were about 1.24x too large at a 952 px input and exact at 1176 px, so the runner uses 1176 px. A second layout confirmed it: 4/4 inside the right shape, with the three squares within 2 px.
4. **Hybrid is fast where it can be.** Using the UIA name when one exists and vision otherwise got 12/12 on a mixed page (3 labeled buttons, 3 unlabeled squares); the name rules alone got 6/12. A UIA lookup took about 2 s. A vision call took a median of 11 s on most pages, but 43 s on one page.
5. **Duplicate labels fooled the naive hybrid.** With two identical "Save" buttons it took the first match and got 4/6 (the first button passed only because it comes first on the page). Treating more than one match as ambiguous and falling back to vision (`hybrid-safe`) got 6/6 on an unseen page, and on the page where I designed the fix.
6. **End-to-end planner loop & model-size termination gap.** Wiring `hybrid-safe` into the LLM planner loop (`mp3`) reached 6/6 (100%) output correctness and 5/6 (83%) clean stops on `qwen2.5:7b`. On a completely unseen page (`unseen1`: new button labels, circles instead of squares, flipped layout, zero prompt changes), `7b` replicated the exact same 6/6 (100%) accuracy and 5/6 (83%) clean stops (38 s median). Across all 12 tasks (`mp3` + `unseen1`), `qwen2.5:3b` hit 12/12 output accuracy but 0/12 clean stops—a clean scaling separation on loop termination.
7. **Bilingual ASR & spoken safety gate.** Unrestricted 99-language Whisper detection with a mixed EN/JA prompt (`asr1`) caused language misdetections (`es`, `tl`, `pt`) and katakana script bleed on English speech (50% WER). Constraining detection to `en`/`ja` only, splitting prompts by language, and switching to `small` (`asr2`, `asr3`) raised language accuracy to 100% on both dev and unseen phrases (0.0% EN WER and 7.4% JA CER on unseen leak-free prompts) while cutting latency by more than half. Risky actions can now be approved or cancelled by voice in English or Japanese, defaulting to cancel on ambiguous speech.

## Failures I found along the way

- Wrong key combination (3B used `ctrl+delete` instead of select-all and delete).
- Repeating the last action instead of finishing (0% clean stop across all `3b` planner runs).
- Prompt regression (`mp2`): adding a generic "done" rule without element-name feedback dropped `3b` from 6/6 to 3/6 and `7b` from 6/6 to 5/6 before `mp3` fixed it.
- A silent wrong click on duplicate labels, reported as success: only the page's own check caught it.
- Whisper script contamination (`asr1`): a mixed EN/JA `initial_prompt` biased Whisper into transcribing English in katakana; a single Japanese homophone slip (`詳細` → `消災`) appeared in `asr3`.
- My own benchmark bugs: typing into a real tab, unverified test setup, and keyboard focus left on the tab strip.

## Limitations

- Small samples (3 to 8 tasks per row); repeats at temperature 0 are not independent.
- Single machine and single speaker (for ASR); CPU timings vary with thermal/power state.
- Synthetic HTML test pages and Notepad; real multi-page web apps with dynamic DOMs are not yet benchmarked.
- The 3B planner was not run on the Edge form page.
- Nepali voice commands are not yet benchmarked.

## How to run

Needs Windows 11 (the Notepad tests use its tabbed Notepad), Python 3.12, Microsoft Edge, [Ollama](https://ollama.com) and, for the voice part, a microphone. `requirements.txt` is pinned to the