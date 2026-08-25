# Module 3 Prompt Library — Application Log

Every prompt in `Module_3_Prompt_Library.pdf` applied to this repository, in
the module's order, with what it produced and what had to be corrected.

Legend: **Applied** = the prompt drove a change in this repo. **Answered** =
the prompt produced analysis, not code. **Already satisfied** = the repo
already met the prompt's requirement before Module 3.

---

## Foundation prompts

| Prompt | Outcome | What happened |
|---|---|---|
| **P0** — start with context | Applied | The project context block was true as written except for one detail: the frontend already existed with a board and modal, so the work started mid-chain rather than at B1 |
| **P1** — verify the assistant reads `app/main.py` | Answered | Framework: FastAPI, app object `app`. Routes actually registered: `GET /health`, `POST /tasks`, `GET /tasks`, `GET /tasks/{task_id}`, `PATCH /tasks/{task_id}`, `DELETE /tasks/{task_id}`. **CORS middleware: not present.** That last answer is what made B4 the first real task |
| **P2** — plan before code | Applied | Plan: CORS → UI states → drag-and-drop → modal polish → contract → tests → break test → log. Each step verified before the next |

---

## Part 3.2 — the board

| Prompt | Outcome | What happened |
|---|---|---|
| **B1** — static Kanban layout | Already satisfied | Three columns existed. Added what B1 asks for and was missing: `data-status` on each column, a subtitle in the header, the description line, `Unassigned` fallback, and an explicit Edit button on every card |
| **B2** — fetch and render | Already satisfied | `fetchTasks()`, a `tasks` array and `renderBoard()` existed. **One bug found:** the priority tie-break used `Number(a.id) - Number(b.id)`, but `app/storage.py` generates UUID string ids, so the comparison was `NaN`. Replaced with `created_at`, then `id`, compared as strings |
| **B3** — loading, empty, ready, error | Applied | Added a `#boardLoading` banner and a board-level error with a Retry button. The error path now calls `renderBoard([])` so the three columns stay visible when the backend is down |
| **B4** — diagnose CORS | Applied | `app/main.py` had no CORS middleware, so no browser page could ever have loaded the board. Added `CORSMiddleware` with four explicit local origins, the five methods used, and `Content-Type` only — no wildcard, no credentials. Verified: `access-control-allow-origin: http://localhost:5500` on a request carrying that `Origin` |
| **B5** — drag-and-drop with PATCH and rollback | Applied | Native HTML5 drag-and-drop, no library. Card carries `data-id`; columns are the drop targets. Optimistic move, then `PATCH {"status": target}`; on a non-OK response the card returns to its previous status and the server's message is shown; a same-column drop returns before any request |

---

## Part 3.3 — the modal

| Prompt | Outcome | What happened |
|---|---|---|
| **C1** — plan the modal flows | Answered | Existing flows to preserve were listed first: create, edit, delete, `.trim()` validation, 422 handling, Escape |
| **C2** — create/edit modal | Applied | Added the × close button, overlay-click dismissal, focus into the title field on open, error clearing on close, and the fix below. Kept the existing POST/PATCH split, trimming, `assignee: null`, and 422-keeps-the-modal-open behavior |
| **C3** — diagnose a failing modal flow | Applied | **Real bug.** The modal always sent `status`, so saving an unchanged task produced `422 Invalid status transition from ToDo to ToDo`. Fixed in the frontend by omitting `status` when it matches the current value. The backend rule was left alone — it is correct, and two Module 2 tests depend on it |

---

## Part 3.4 — refactor

| Prompt | Outcome | What happened |
|---|---|---|
| **D1** — 8-behavior contract | Applied | `docs/module3_behavior_contract.md`, ten items with the manual check and the observed result for each |
| **D2** — refactor one selected section | Applied | One bounded refactor: `showLoadError` became `showBoardError(message, { withRetry })`. URLs, methods, body shapes, status values, class names, ids and `data-*` attributes were all left unchanged |
| **D3** — review a diff for regression risk | Applied | The review caught its own regression: the first drag-error version reused the load error, so a rejected drag displayed a "Retry" button that would re-fetch the board for no reason. Retry is now load-errors only |
| **D4** — recover one regression surgically | Not needed | No behavior-contract item regressed. Re-checked C1–C10 after the refactor |

---

## Part 3.5 — test and debug

| Prompt | Outcome | What happened |
|---|---|---|
| **E1** — brainstorm PATCH edge cases | Applied | Six uncovered scenarios, ranked for the drag/modal frontend — `docs/module3_edge_cases.md` |
| **E2** — generate one pytest test | Applied | Seven tests using the existing `client` / `created_task` fixtures. Each asserts the status code *and* the response content. 17 → 24 passing |
| **E3** — prove a test by deliberate breakage | Applied | Two breaks, both predicted before running: allowing `Done -> ToDo` (1 predicted failure, 1 seen) and forcing the transition check on every PATCH (3 predicted, 3 seen). Both restored — `docs/module3_break_test.md` |
| **E4** — diagnose pytest failure | Answered | Used on the break-test failures. No assertion was weakened and no test was edited to go green |

---

## Deliverable and extensions

| Prompt | Outcome | What happened |
|---|---|---|
| **R1** — debugging log and reflection | Applied | `docs/module3_debug_log.md`, written from observed runs only |
| **O1** — accessibility review | Partly applied | Free, safe items taken: `role="dialog"`/`aria-modal` on the modal, `aria-label` on the close button, `role="status"`/`aria-live` on the loading banner, `role="alert"` on the board error, and a visible `:focus-visible` outline. Left as optional: keyboard-accessible drag-and-drop, which needs a real alternative control rather than a tweak |
| **O2** — visual polish | Partly applied | Only behavior-carrying CSS: the `.drag-over` drop highlight, `.dragging` opacity, and the loading/error banner styles. Existing colors, fonts and class names untouched |

---

## Files changed

| File | Change |
|---|---|
| `app/main.py` | CORS middleware for the local frontend origins (B4). No route touched |
| `frontend/index.html` | UI states, drag-and-drop with rollback, modal fixes, sorting fix, accessibility attributes |
| `tests/test_tasks.py` | Seven PATCH tests appended (E2) |
| `docs/module3_*.md` | Contract, edge cases, break test, debugging log, this log |
