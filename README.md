# AI Interview Simulator

Mock technical interviews with an AI interviewer: timed, realistic scenarios with live AI
pair-programming, session logging, and rubric-based feedback to track your progress across attempts.

A local practice environment for an experienced TypeScript/Node engineer getting fluent in
Python ahead of a senior full-stack interview, with timed mock AI-assisted coding interviews.
Click the date badge in the top bar to set your interview date for a countdown (stored locally in
`backend/data/settings.json`, which is gitignored). "Acme Health" is a fictional company used for
the scenarios.

- **15 Python syntax drills** (5–15 min each): dicts, lists, comprehensions, collections, functions & type hints, None handling, strings, sorting, filtering, exceptions, context managers, classes, dataclasses, async/await.
- **1 interview-style project** (`proj1`, 60–90 min): a multi-file telehealth booking service (FastAPI, SQLAlchemy, timezones, idempotency, domain errors). Part 1 is debugging; parts 2–4 add features to an unfamiliar codebase, the format of CodePair-style and AI-assisted rounds.
- **5 FastAPI debugging challenges** in a fictional mental-health clinic app (FastAPI + SQLAlchemy + SQLite + Pydantic v2): eligibility rules, missing records, date sorting, validation errors, and stale frontend data (React + backend cache).
- **Dashboard** (React + TS + Vite): pick an exercise, read the requirements, open the file in VS Code, run the tests, see pass/fail per test, reveal hints one at a time, and track progress.
- **TS → Python cheat sheet** in the dashboard (source: [`docs/ts-to-python.md`](docs/ts-to-python.md)).
- **Clinic App tab**: a small front-desk UI so you can *see* each debugging bug as a user would.

Every exercise starts broken or incomplete. Reference solutions are kept separately in `backend/solutions/`
and the dashboard never shows them.

---

## Setup on Windows 11

**Prerequisites.** Install these once, then open a *new* terminal so PATH refreshes:

```powershell
winget install --id=astral-sh.uv -e          # Python package/project manager (also installs Python 3.12 for you)
winget install --id=OpenJS.NodeJS.LTS -e     # Node.js 20+
winget install --id=Microsoft.VisualStudioCode -e   # if you don't have it
```

**Install and start:**

```powershell
cd path\to\interview-trainer
.\setup.cmd      # uv sync, npm installs, creates your exercise copies, runs a self-check
.\start.cmd      # starts all 3 servers and opens http://127.0.0.1:5173
```

`setup.cmd` / `start.cmd` work from cmd, PowerShell, Windows Terminal, or a double-click. They call
PowerShell with `-ExecutionPolicy Bypass` for the setup script only, so you don't need to change any
system policy. Press **Ctrl+C** in the terminal to stop everything.

In VS Code: **File → Open Folder** on this directory and accept the recommended extensions prompt.

## Setup on macOS / Linux

```bash
brew install uv node        # or your package manager
./setup.sh
./start.sh
```

## What's running

| Process | URL | Source |
|---|---|---|
| Dashboard (Vite) | http://127.0.0.1:5173 | `frontend/` |
| Trainer API | http://127.0.0.1:8710/docs | `backend/trainer/` (infrastructure, no need to edit) |
| Clinic API (the app you debug) | http://127.0.0.1:8711/docs | `backend/workspace/clinic/` (auto-reloads on save) |
| Booking API (the project) | http://127.0.0.1:8712/docs | `backend/workspace/booking/` (auto-reloads on save) |
| Payouts API (mock AI interview #1) | http://127.0.0.1:8713/docs | `backend/workspace/payouts/` (portal: http://127.0.0.1:5173/payouts.html, `frontend/src/payouts/`) |
| Remits API (mock AI interview #2) | http://127.0.0.1:8714/docs | `backend/workspace/remits/` (UI: http://127.0.0.1:5173/remits.html, `frontend/src/remits/`) |
| Earnings API (mock AI interview #3) | http://127.0.0.1:8715/docs | `backend/workspace/earnings/` (UI: http://127.0.0.1:5173/earnings.html, `frontend/src/earnings/`) |

All of them run via `npm run dev` (using `concurrently`). Each can also run alone: `npm run dev:trainer`, `npm run dev:clinic`, `npm run dev:booking`, `npm run dev:web`.

## Daily workflow

1. In the dashboard, pick an exercise and read the requirements.
2. Write code in the **built-in editor** (Monaco, the editor from VS Code). The test files are in read-only tabs.
3. Press **Ctrl/⌘+Enter** to save and run the tests. **Ctrl/⌘+S** saves only. Failing tests expand to show the assertion and traceback.
4. Stuck? **Show hint**. Hints are progressive and never contain the full answer.
5. When all tests pass, the exercise is marked complete automatically.

**Requirements and full screen.** Every exercise has a read-only **REQUIREMENTS.md** pinned at the top of the
file tree (rendered as a preview; **Source** shows the markdown). **⛶ Full screen** turns the page into an IDE:
editor on the left, test results and hints on the right (**Hide panel** for more room), and ‹ › plus a dropdown
to move between exercises. It's remembered for the next exercise. **Esc** (outside the editor) exits.
Drag the dividers to resize the file tree and the side panel. Drag one almost shut, or double-click it, to collapse
that column to a thin rail (click the rail to bring it back). **Ctrl/⌘+B** toggles the file tree. Sizes are remembered.

**Split editor** (◫ in the tab bar, or **Ctrl/⌘+\\**): two panes side by side, each with its own tabs, e.g.
your code on the left and the tests on the right. The file tree opens files in the pane you last clicked.
Drag a tab onto the other pane's tab bar to move it; drag the divider to resize (double-click for 50/50);
⊟ closes a side. Both panes can show the same file and stay in sync.

**Mock AI interviews** (last section of the list). Timed, 60-minute simulations of the AI coding interview, three
scenarios in the provider-payments world, each its own full-stack codebase (FastAPI + React/TS) with a user-reported bug:
**#1** provider payouts, **#2** claims & payer remittances, **#3** rates & earnings. When the bug's tests pass, three
feature requests unlock; pick one. Do them in order on different days to see how you improve: the start and review
screens show **Your attempts** side by side (time to fix, prompts, test runs, narration, and the grader's 1–4 scores),
and the grader compares each attempt with your earlier ones. **Sandbox** (first in the list) is a 15-minute demo on a
tiny app for showing the screen off: clicking it opens the interview straight away, it has its own session slot (it never
ends a real interview in progress) and it isn't counted in Your attempts. The panel next to the editor has:

- **AI assistant**: Claude, through your local Claude Code login (`claude` on PATH, no API key needed). It can read,
  search and edit the app's code and run its backend tests, like the assistant built into CodeSignal. It can't see
  the reference solutions or the interviewer's notes. The editor saves before each prompt and reloads files Claude edits.
- **Interviewer**: Claude playing the interviewer. Ask domain and product questions; it won't give away the answer.
- **App**: the app's UI running your workspace code. **Narrate**: think out loud (speech to text in Chrome) or type notes.

Every prompt, reply (with the tools Claude used and the files it edited), test run and note is logged with a timestamp in
`backend/data/interview/<session>/`. **End interview** shows the timeline and your diff, and **Grade my interview** has
Claude grade the session against the interview's criteria. Set `TRAINER_CLAUDE_MODEL` (e.g. `sonnet`) to pick the model.

**Quick ref.** The panel beside the editor has a **Quick ref** tab: one-screen docs for each data structure and
library (dict, list/tuple, set, str, collections, comprehensions, sorting, None, exceptions, classes, dataclasses,
async, datetime, SQLAlchemy, Pydantic, FastAPI...). The pages for the current exercise come first, and the search box
covers all of them. Source: [`docs/quickref/`](docs/quickref), one Markdown file per page; add a page there and list it
in an exercise's `quickref = [...]` in `backend/catalog.toml`.

**File explorer and navigation.** The editor has a file tree (☰ Files) with a filter box. The debugging
challenges show the whole clinic app, and the project shows the whole booking service. Files open in tabs. **F12** or
**⌘/Ctrl+click** jumps to a definition in another file, which is the fastest way to learn an unfamiliar codebase.
The project's results are grouped by part.

**Readable failures.** Test failures show only *your* frames (test → router → service → error), not dozens
of FastAPI/Starlette internals. Exception messages and pytest's assertion diffs are unchanged.

**IntelliSense in the browser editor.** Python completions, hover docs and signature help come from
[Jedi](https://github.com/davidhalter/jedi), which runs against the project's `.venv` and so knows FastAPI, SQLAlchemy and Pydantic.
Squiggles come from Ruff and Jedi as you type. The TypeScript file in dbg5 uses Monaco's built-in TS language service.
Untick **IntelliSense** to practice the way CoderPad-style interview editors work, without autocomplete. The setting is remembered.

**Using your own IDE.** Choose WebStorm, VS Code or PyCharm under the editor and click **Open file**. Edits sync both ways: the
browser editor re-reads files whenever you switch back to the tab, and never overwrites text you haven't saved. WebStorm has
no real Python support (JetBrains' Python plugin doesn't run in it), so the browser editor gives better Python IntelliSense.
For WebStorm/PyCharm to be found on Windows, enable *Shell scripts* in JetBrains Toolbox settings.

You can also run tests from a terminal:

```bash
uv run pytest backend/tests/drills/test_ex05_functions.py      # one drill
uv run pytest backend/tests/clinic -k eligibility -x -vv        # filter by name, stop at first failure
npm test --prefix frontend                                       # the vitest half of dbg5
```

## How the files are organized

```
backend/
  starters/      pristine broken versions (never edit, used by reset)
  workspace/     YOUR working copies (gitignored), created by setup  ← edit these
    drills/        ex01_dicts.py … ex15_async_patterns.py
    clinic/        the FastAPI clinic app (debugging challenges)
    booking/       the booking service (interview project, start with its README.md)
  solutions/     reference solutions (separate on purpose; the dashboard never shows them)
  tests/         pytest suites (drills/, clinic/, booking/, trainer/)
  trainer/       dashboard API: catalog, runner, progress
  catalog.toml   exercise list: requirements, hints, files, tests
  data/          SQLite DBs: progress.db (your progress), clinic.db + booking.db (demo data)
frontend/
  src/           dashboard + Clinic App tab
  src/clinic/patientState.ts   YOUR working copy for dbg5 (frontend half)
  tests/         vitest suite for dbg5
docs/ts-to-python.md           the cheat sheet
```

## Resetting an exercise

Reset restores the original broken starter file(s) and clears that exercise's progress (status, hints,
attempts). Your lifetime "completed N×" count is kept.

- **Dashboard:** open the exercise → **Reset exercise…** → **Yes, reset**.
- **Command line:**

  ```bash
  npm run reset -- py03               # one exercise
  npm run reset -- dbg2 dbg5          # several
  npm run reset -- proj1              # the whole booking project (every file in it)
  npm run reset -- --all              # everything
  npm run reset -- py03 --keep-progress   # restore files only
  npm run status                      # which exercises have you modified?
  ```

  (Equivalent to `uv run python scripts/workspace.py reset py03`.)

- **Start completely fresh:** delete `backend/workspace/`, `frontend/src/clinic/patientState.ts`
  and `backend/data/`, then run `uv run python scripts/workspace.py init`. The servers also recreate missing files on startup.

To reset the clinic demo data (patients, appointments), stop the servers and delete `backend/data/clinic.db`. It is re-seeded on the next start.

## Debugging in VS Code

`.vscode/launch.json` contains:

| Configuration | Use it for |
|---|---|
| **Pytest: current test file** | Open a test file, set breakpoints in your exercise code, press F5. |
| **Pytest: pick an exercise's tests** | Choose a test file from a list. |
| **Clinic API (debug, port 8711)** | Breakpoints inside FastAPI endpoints. First stop the normal clinic server: run `npm run dev:no-clinic` instead of `npm run dev`, so port 8711 is free and the dashboard keeps working. |
| **Python: current file** | Run or debug a scratch script. |

The **Testing** panel (beaker icon) also discovers every pytest test. Right-click → *Debug Test*.

Recommended extensions: Python, Pylance, Python Debugger, Ruff, Even Better TOML, Vitest.

## Verifying the training content

```bash
npm run verify     # in a temp dir: every starter must FAIL, every reference solution must PASS
uv run pytest backend/tests/trainer   # catalog/self-checks
```

`npm test` runs every exercise test against *your* working copies, so it fails until you've solved everything.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `'uv' is not recognized` right after installing | Open a new terminal (PATH refresh) or sign out and back in. |
| `Port 5173/8710/8711 is already in use` | A previous run is still alive. Close old terminals, or `netstat -ano \| findstr :8710` then `taskkill /PID <pid> /F`. |
| Clinic App tab says "Clinic API unavailable" | Probably a syntax error in your clinic edits. Read the `clinic` lines in the terminal. It reloads on save. |
| Dashboard says it can't reach the trainer API | Check the `trainer` lines in the terminal. Re-run `setup.cmd` if dependencies are missing. |
| "Open in VS Code" does nothing | Use the `vscode://` link shown, or reinstall VS Code with **Add to PATH** checked, then restart `start.cmd`. |
| Antivirus slows the first test run | The first pytest/vitest run warms caches; later runs are faster. You can exclude this folder. |
| Windows long-path errors in `node_modules` | Clone to a short path such as `C:\dev\interview-trainer`. |
