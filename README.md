# VoiceHands

A local, voice-controlled Windows agent, plus a benchmark that compares three ways of finding what to click: the accessibility (UI Automation) tree, a vision model reading a screenshot, and a hybrid of the two.

Everything runs locally on one Windows laptop: faster-whisper (speech), Ollama (qwen2.5 text models and qwen2.5vl:7b for vision), pywinauto and pyautogui (observe and act).

## Results

| Experiment | Tag | Model or mode | Tasks | Runs | Correct | Median s |
|---|---|---|---|---|---|---|
| Notepad, 8 typing tasks, LLM planner on the UIA tree | v5 | qwen2.5:3b | 8 | 8 | 6/8 | 73 |
|  | v5 | qwen2.5:7b | 8 | 8 | 8/8 | 175 |
| Edge form page, 3 tasks, LLM planner on the UIA tree | bu1 | qwen2.5:7b | 3 | 3 | 3/3 | 342 |
| Edge page with unlabeled shapes, 4 tasks, LLM planner on the UIA tree | hu1 | qwen2.5:3b | 4 | 8 | 0/8 | 64 |
|  | hu1 | qwen2.5:7b | 4 | 8 | 0/8 | 122 |
| Same unlabeled page, screenshot-only (vision model) | hv1 | qwen2.5vl:7b | 4 | 4 | 4/4 | 11 |
| Edge page, 3 labeled buttons + 3 unlabeled squares, grounding modes | mx1 | hybrid | 6 | 12 | 12/12 | 6 |
|  | mx1 | uia-rules | 6 | 12 | 6/12 | 2 |
|  | mx1 | vision-7b | 6 | 12 | 12/12 | 11 |
| Duplicate-label page A, grounding modes | dp1 | hybrid | 3 | 6 | 4/6 | 2 |
|  | dp1 | uia-rules | 3 | 6 | 4/6 | 2 |
|  | dp1 | vision-7b | 3 | 6 | 6/6 | 43 |
| Duplicate-label page B (unseen), grounding modes | dp2 | hybrid | 3 | 6 | 4/6 | 2 |
|  | dp2 | hybrid-safe | 3 | 6 | 6/6 | 44 |
|  | dp2 | uia-rules | 3 | 6 | 4/6 | 2 |
|  | dp2 | vision-7b | 3 | 6 | 6/6 | 11 |
| Page A re-run with hybrid-safe (fix was designed on this page) | dp3 | hybrid-safe | 3 | 6 | 6/6 | 42 |

How to read the table: Tasks is the number of distinct tasks, Runs is tasks times repeats, and Correct counts runs. Repeats at temperature 0 are not independent samples. Every result is checked by code, not by eye: Notepad's text is read back, and the test pages write what was clicked into their own tab title. Seconds are the median per run; they include model loading, vary a lot on this laptop, and should not be compared across rows.

## What I found

1. **Notepad, UIA tree + LLM planner.** qwen2.5:7b got 8/8 outputs right and said "done" on 7 of 8 tasks. qwen2.5:3b got 6/8 outputs right and was about 2.4x faster (median 73 s vs 175 s), but never said "done" (0/8): it repeated its last action until a loop guard stopped it. On the Edge form page, 7B also repeated its final Submit click in all 3 tasks (only the 7B planner has results on that page).
2. **Unlabeled elements break the UIA tree.** On a page of unlabeled coloured shapes (4 tasks, run twice), the UIA-tree agent got 0/8 with both models.
3. **Vision can find them.** qwen2.5vl:7b clicked all 4 shapes correctly. Its coordinates were about 1.24x too large at a 952 px input and exact at 1176 px, so the runner uses 1176 px. I did not find the cause. A second layout confirmed it: 4/4 inside the right shape, with the three squares within 2 px.
4. **Hybrid is fast where it can be.** Using the UIA name when one exists and vision otherwise got 12/12 on a mixed page (3 labeled buttons, 3 unlabeled squares); the name rules alone got 6/12. A UIA lookup took about 2 s. A vision call took a median of 11 s on most pages, but 43 s on one page, and I did not find out why.
5. **Duplicate labels fooled the naive hybrid.** With two identical "Save" buttons it took the first match and got 4/6 (the first button passed only because it comes first on the page). Treating more than one match as ambiguous and falling back to vision got 6/6 on an unseen page, and on the page where I designed the fix.

## Failures I found along the way

- Wrong key combination (3B used ctrl+delete instead of select-all and delete).
- Repeating the last action instead of finishing.
- A silent wrong click on duplicate labels, reported as success: only the page's own check caught it.
- My own benchmark bugs: typing into a real tab, unverified test setup, and keyboard focus left on the tab strip.

## Limitations

- Small samples (3 to 8 tasks per row); repeats at temperature 0 are not independent.
- One laptop; timings vary a lot and I did not isolate why (battery power may have throttled some runs).
- Synthetic test pages; the planner prompt was written around Notepad.
- The 3B planner was not run on the Edge form page.
- The vision runner does single clicks, not a multi-step loop yet.

## How to run

Needs Windows 11 (the Notepad tests use its tabbed Notepad), Python 3.12, Microsoft Edge, [Ollama](https://ollama.com) and, for the voice part, a microphone. I have only run this on one machine. I tested one fresh clone there: the install, the imports and `benchmark\report.py v5` (which reproduces the table row) work. I did not re-run the mouse-controlling benchmarks or the voice part from a clean clone. `requirements.txt` is pinned to the versions my results came from: a first install with unpinned requirements got newer numpy and onnxruntime releases, and Windows Application Control blocked numpy's DLL. The pinned versions loaded fine, which suggests but does not prove that the versions were the cause.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b
ollama pull qwen2.5vl:7b
```

**The benchmarks control your real mouse and keyboard.** Don't touch either during a run. Moving the mouse into a screen corner stops everything. Each Notepad test uses its own file (`logs/bench_scratch.txt`) and each Edge test opens its own window. Close old test windows before a run, and don't keep unsaved work in Notepad.

Reproduce results (use your own tag so your runs stay separate from mine):

```powershell
$env:VH_AUTO="1"          # don't pause on "risky action" prompts
$env:VH_TAG="mine1"       # your label for this run
$env:VH_MODEL="qwen2.5:7b"
python benchmark\run_bench.py 1            # Notepad: UIA tree + LLM planner
python benchmark\run_browser.py 1          # Edge form page: UIA tree + LLM planner
python benchmark\run_hard.py 1             # unlabeled shapes: UIA tree + LLM planner
python benchmark\run_vision.py 1           # same page, screenshot only (qwen2.5vl:7b)
python benchmark\run_mixed.py hybrid 2     # modes: uia | vision | hybrid
python benchmark\run_dup2.py safe 2 b      # modes: uia | vision | hybrid | safe; pages: a | b
python benchmark\report.py mine1           # summary and task matrix for your tag
```

On my laptop a planner task took 1 to 8 minutes and a vision call took tens of seconds.

Voice control (not part of the benchmark):

```powershell
python voice_main.py
```

Press Enter, say a command, press Enter. It shows what it heard and asks y/n before acting. It then drives the first Notepad window it finds, so open a blank Notepad tab first. The first run downloads the Whisper `medium` model (over 1 GB). What it hears is saved to `logs/asr.jsonl`, which is not committed.
