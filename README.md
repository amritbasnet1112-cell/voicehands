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
