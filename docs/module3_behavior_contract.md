# Module 3 Behavior Contract (Prompt D1)

Written **before** the refactor and re-checked after it. The rule the module
teaches: you cannot tell whether a refactor was safe unless you wrote down what
must not change.

Every "Pass/Fail notes" entry below records a check that was actually run
against the running app (`uvicorn` on `http://127.0.0.1:8000`, page served from
`http://localhost:5500/frontend/index.html`), not a check that was merely
planned.

| ID | Behavior | How to check manually | Pass/Fail notes |
|---|---|---|---|
| C1 | Three status columns render with correct counts | Open the board with tasks in the API; read the `(n)` next to each column heading | **Pass** — with 4 seeded tasks the headings read To Do (3), In Progress (1), Done (0) |
| C2 | Cards sort by priority inside each column | Seed High, Medium and Low tasks in one status; read the card order top to bottom | **Pass** — To Do rendered High, High, Low. Ties now break by `created_at` then `id` |
| C3 | Loading state appears before tasks load | Throttle the network (or slow `fetch`) and reload; the "Loading tasks…" banner must be visible while `GET /tasks` is pending | **Pass** — banner visible during an 800 ms delayed fetch, hidden after the response |
| C4 | Empty columns remain visible and stay drop targets | Delete every Done task and reload | **Pass** — Done column stays with `(0)` and a "No tasks" placeholder; a card can still be dropped on it |
| C5 | Error state appears when the backend is stopped | Stop `uvicorn`, click Retry or reload | **Pass** — board-level error with a Retry button, three columns still rendered with `(0)`. Retry re-loaded the board after `uvicorn` restarted |
| C6 | Valid drag sends PATCH and updates the board | Drag a To Do card onto In Progress; watch the Network tab | **Pass** — `PATCH /tasks/{id}` with `{"status":"InProgress"}` returned 200 and the card stayed in the new column |
| C7 | Invalid drag / server 422 reverts and shows the server message | Drag a To Do card onto Done (an illegal transition) | **Pass** — card returned to To Do and the board showed *Invalid status transition from ToDo to Done. Allowed transitions: [...]* |
| C8 | Modal create/edit flows still work, including title validation and dismissal | Open New Task with a whitespace title; then create a real task; then edit a task; then close with Cancel, ×, Escape and an overlay click | **Pass** — whitespace title showed "Title is required." and sent **zero** requests; create sent `POST` then `GET`; edit sent `PATCH` then `GET`; all four dismissal paths closed the modal and cleared the error |

## Extra invariants this build added

| ID | Behavior | Why it is in the contract |
|---|---|---|
| C9 | A same-column drop sends no request at all | Dropping a card back where it started must not produce a `Done -> Done` 422. Verified by counting `fetch` calls: 0 |
| C10 | An edit that does not change the status omits `status` from the PATCH body | The backend rejects same-to-same transitions with 422, so a title-only edit of a Done task would otherwise fail. Guarded by `test_patch_title_only_on_done_task_returns_200` |

## Checklist form (for the debugging log)

- [x] C1 counts
- [x] C2 priority sorting
- [x] C3 loading
- [x] C4 empty columns visible
- [x] C5 error + Retry
- [x] C6 valid drag PATCHes
- [x] C7 invalid drag reverts with the server message
- [x] C8 modal create/edit/validation/dismissal
- [x] C9 same-column drop is a no-op
- [x] C10 unchanged status is omitted from PATCH
