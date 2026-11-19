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