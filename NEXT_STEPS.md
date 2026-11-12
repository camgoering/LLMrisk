# Finishing the LLM portion — step by step

Everything is set up. What's left is the ChatGPT runs (only you can do these), then
analysis and write-up (Claude can do most of it). Roughly **2 hours of runs**, which
can be split across sessions.

Tick boxes as you go.

---

## Step 0 — Get the latest files (2 min)

In PowerShell, in the `LLMrisk` folder:

```powershell
git pull
python make_runs.py
```

Until the Profiles sheet is filled it writes the 31 P1 files only; that's expected.

- [ ] `git pull` done
- [ ] `make_runs.py` runs (31 of 62 until Profiles is filled)

## Step 1 — Get the profile figures from Jules

Under the division of labor, sourcing the US averages is Jules's job. The team's
calculation uses the same figures as its survey defaults, which is what makes your
P2 numbers comparable to theirs. Ask Jules (or whoever owns the team's defaults)
for these four values **and their sources**:

| Profiles column | Team default it must match |
|---|---|
| Annual Income (USD) | "Default is U.S. avg wage" |
| Credit Tier | "Estimated Credit Score Quadrant… Default is U.S. avg": which quadrant (Poor / Fair / Good / Excellent) |
| Available Credit (USD) | whatever the team's calculation uses for that tier ("Default is average U.S. credit limit") |
| Savings (USD) | "Default is U.S. avg savings" |

Type them into `data/llm_run_log.xlsx` → **Profiles**, row `US_AVG`, with the
sources in column F. Save, close, then:

```powershell
python make_runs.py
```

Now it should say **62 of 62**.

If the team's credit figure is still the planning doc's table ($0 / $500 / $1,000 /
$1,500, no source), use whatever they actually settle on. Your job is to match
their inputs, not fix them.

**Don't start the runs until these are in.** The P1 calibration run doesn't need
them, but the P2 one does.

- [ ] Figures + sources from Jules
- [ ] Typed into Profiles; `make_runs.py` says 62 of 62

## Step 2 — Set up ChatGPT (5 min, once)

1. Decide which model you'll use and **stick with it for all 62 runs**. Pick it in
   the model menu and take a screenshot showing the model name. Save it as
   `data/model_screenshot.png`.
2. Settings → Personalization:
   - **Memory: off**
   - **Reference chat history: off**
   - **Custom instructions: blank**
3. Simplest option: use **Temporary Chat** for every run (the toggle at the top of
   a new chat). It never uses memory and doesn't clutter your history.
4. Don't turn on web search.
5. Fill in the table in `METHODOLOGY.md` §1: product, model name as shown, account
   tier (free/Plus), and the date you start.

- [ ] Model chosen + screenshot saved
- [ ] Memory / chat history / custom instructions off
- [ ] METHODOLOGY §1 filled in

## Step 3 — How to do ONE run (about 1–2 min each)

Open `runs/SCHEDULE.csv` in Excel next to `data/llm_run_log.xlsx`. Go down the
schedule in order. For each row:

1. **New chat** (Temporary Chat). Never reuse a chat.
2. Open the run's file from `runs/` in Notepad, e.g. `runs/003_P1_PayPal.txt`.
3. **Ctrl+A, Ctrl+C**, click in ChatGPT, **Ctrl+V**, **Enter**.
4. Wait for the full answer. **Don't regenerate, don't reply, don't edit.**
5. Copy the whole answer (the copy icon under the response).
6. Log it in `data/llm_run_log.xlsx` → **Run Log**, one row per run:

| Column | What to put |
|---|---|
| Run ID | the `run_id` from SCHEDULE.csv |
| Date | today, e.g. 2026-11-13 |
| Model Version | exactly as in your screenshot |
| Prompt | P1 or P2 (dropdown) |
| Service | dropdown |
| Profile | `US_AVG` |
| Annual Risk USD | the number — see decision rules below |
| Low USD / High USD | P2 gives these; P1 only if it gives a range |
| Refused | `Y` if no dollar figure at all, otherwise `N` |
| Truncated | `N` (unless step 4 below says otherwise) |
| Top Data Types | P2's TOP_DATA_TYPES line; blank for P1 |
| Raw Response | **paste the whole answer** — see tip below |
| Notes | anything odd: `midpoint`, `converted from monthly`, `searched`… |
| Round | the `round` from SCHEDULE.csv (0 for runs 1–2) |
| Calibration | `Y` for runs 1–2, `N` for everything else |

7. Close the chat. Next row.

**Excel tip for Raw Response:** if you just click a cell and paste, a multi-line
answer gets split across many rows. Instead, **click the cell, then click in the
formula bar at the top** (or press **F2**), then paste. It all goes into one cell.

**Decision rules** (full list in `METHODOLOGY.md` §9 — don't improvise):

- One number → that's Annual Risk USD.
- A range only (e.g. "$50–$500") → Low = 50, High = 500, Annual = 275 (the
  midpoint), Notes: `midpoint`.
- Several scenarios → the one called "most likely"/"typical"; if none, the lowest.
  Note it.
- Monthly → ×12. Lifetime → convert to annual. Note it.
- No number at all → Refused = Y, dollar cells blank, still paste the response.

## Step 4 — Calibration: runs 1 and 2 (5 min)

These are PayPal P1 and P2. They test the workflow and are **not counted**.

- If ChatGPT says the message is **too long**: stop and send Claude the exact
  error. METHODOLOGY §2.4 covers this (a fixed cutoff for every service), and the
  run files will need regenerating.
- If run 2 (P2) doesn't come back in the five-line format, note it but carry on;
  the decision rules handle it.
- Look at the Summary sheet: PayPal should still show **n = 0**. That proves
  calibration rows are being excluded.

- [ ] Run 1 logged (Calibration = Y)
- [ ] Run 2 logged (Calibration = Y)
- [ ] No "too long" error; Summary shows n = 0 for PayPal

## Step 5 — Round 1: runs 3–14 (about 20 min)

Do all twelve. Then check the Summary sheet: every P1 and P2 cell for the six
services should show n = 1 (or a refusal).

Only look for **procedure** problems here (wrong column, missing rounds). **Do not
change anything because of the numbers** — that would contaminate the data.

- [ ] Round 1 done (runs 3–14)

## Step 6 — Rounds 2–5: runs 15–62 (about 1.5 hours)

Same thing, four more times. Rounds can be split across days. Do whole rounds at a
time if you can, and finish all five rounds within a few days so the model doesn't
change underneath you.

- [ ] Round 2 (runs 15–26)
- [ ] Round 3 (runs 27–38)
- [ ] Round 4 (runs 39–50)
- [ ] Round 5 (runs 51–62)

**Short on time?** Stop after round 3. Three repeats still gives a standard
deviation. Note it in the write-up. Don't drop services.

Fill in the last collection date in METHODOLOGY §1.

## Step 7 — Get the team's six numbers

Ask the team for their calculated annual risk (USD) for PayPal, X, Google,
ChatGPT, Netflix and LinkedIn, using the profile numbers from step 1. Type them
into **Comparison** column D. Spearman's rho appears in cell B21.

If they aren't ready, skip this step. You can hand over the workbook and they fill
in column D themselves.

- [ ] Team figures entered (or skipped)

## Step 8 — Push and hand back to Claude

```powershell
git add data/llm_run_log.xlsx data/model_screenshot.png METHODOLOGY.md
git commit -m "Runs complete"
git push
```

Then start a Claude session on this repo and say:

> Runs are done and pushed. Continue from NEXT_STEPS step 9.

## Step 9 — What Claude does next (you review)

1. Runs `analyze.py` and checks the log for anything breaking the decision rules
2. Fills every `[blank]` in `writeup/llm_section.md` with the real numbers, tables
   and discussion
3. Converts the section to LaTeX for John's report (or Word if the team prefers)
4. Makes a clean handoff copy of the workbook (working instructions removed, a short
   "what each sheet is" note added)
5. Optionally a chart or two for the presentation (CV by service, LLM vs team rank)

## Step 10 — Hand off to the team

Two files:

1. **The workbook** — all runs, summary statistics, comparison
2. **The report section** (LaTeX or Word) — methods, results, limitations, ethics,
   prompts in the appendix

## For the presentation (Nov 17 / 19 / 24 — live demo)

A good live demo takes 60 seconds: open a fresh Temporary Chat, paste one P2 run
file, show the answer, then open the Summary sheet to show how much that number
varies across five runs. The variability is the point. Don't log the demo run.
