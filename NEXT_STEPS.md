# Finishing the LLM portion — step by step (prompts v2.0)

**What changed (Nov 18):** both prompts now also ask for a **risk grade A–E**, P2
also asks for its **sources**, and every answer is checked for a **ToS;DR**
mention. That means starting the runs again. The first P1 run (Nov 12) isn't
wasted: it's kept as a **pilot** in `data/archive/` and shows whether adding the
grade question changes the dollar figures.

**Plan:** all 62 runs in one sitting (or two close together), P1 and P2
**alternating within each round**, about 1.5–2 hours with the helper.

Tick boxes as you go.

---

## Step 0 — Get the latest files (2 min)

In PowerShell, in the `LLMrisk` folder:

```powershell
git pull
```

`data/llm_run_log.xlsx` is now a **fresh, empty** workbook with three new Run Log
columns: Risk Grade, Cites ToS;DR, Sources (P2). Your old runs are in
`data/archive/llm_run_log_v1_pilot.xlsx`.

- [ ] `git pull` done

## Step 1 — Profile values (5 min)

Open `data/llm_run_log.xlsx` with `start data\llm_run_log.xlsx`. On the
**Profiles** sheet, row `US_AVG`, fill in:

| Column | What |
|---|---|
| Annual Income (USD) | the value the team's calculation uses |
| Credit Tier | the credit-score quadrant (Poor / Fair / Good / Excellent) |
| Available Credit (USD) | the team's credit limit for that quadrant |
| Savings (USD) | the value the team's calculation uses |
| Source / citation | where each number came from |

**Use the same values as the team's calculation**, or the comparison doesn't hold.

**With only 5 survey responses:** don't use the median, because with five people
the median is one person's actual answer. Use the team's US-average defaults, or the
rounded mean, and never an individual's answers.

Save, **close Excel**, then:

```powershell
python make_runs.py
```

It should say **62 of 62 run files written**.

- [ ] Profile filled with sources
- [ ] `make_runs.py` says 62 of 62

## Step 2 — ChatGPT setup (2 min)

Same as before: same model (it said **GPT-6** last time; if it shows something
else, use that and tell Claude), **Temporary Chat**, Memory and chat history off,
no web search.

- [ ] Model name noted

## Step 3 — Run them

**Close the workbook in Excel**, then:

```powershell
python log_run.py
```

For each run:

1. The prompt is on your clipboard. **New Temporary Chat → Ctrl+V → Enter.** Wait
   for the whole answer. Don't regenerate or reply.
2. Click ChatGPT's **copy button**, go back to PowerShell, press **Enter**.
3. **Dollar figure:**
   - **P2:** it reads the seven-line answer. Press Enter if it's right.
   - **P1:** it lists the dollar amounts. Type the one the rules pick: a number, a
     range like `50-500` (no point estimate), or `R`.
4. **Grade** (new):
   - **P2:** it reads `RISK_GRADE`. Press Enter if it's right.
   - **P1:** it lists grade mentions and suggests one. Press Enter or type a letter.
     Leave blank if there's no grade.
5. **ToS;DR** (new): it checks automatically. If it finds a mention, it shows you
   the passage, and you press Enter to count it. If not, it says "not mentioned"
   and moves on.
6. Optional note, Enter. The row is written and the answer saved to
   `data/responses/`.
7. Enter for the next run, or `q` to stop. Running `python log_run.py` again
   picks up where you left off.

**Order:** runs 1–2 are calibration (PayPal P1, PayPal P2, not counted). Then
five rounds of 12: six services under P1, then the same six under P2.

| Round | Runs |
|---|---|
| Calibration | 1–2 |
| 1 | 3–14 |
| 2 | 15–26 |
| 3 | 27–38 |
| 4 | 39–50 |
| 5 | 51–62 |

At the end of each round it tells you, and you can open the workbook to check the
Summary sheet (close it again before continuing).

- [ ] Calibration (1–2)
- [ ] Round 1 (3–14)
- [ ] Round 2 (15–26)
- [ ] Round 3 (27–38)
- [ ] Round 4 (39–50)
- [ ] Round 5 (51–62)

**Short on time?** Stop after round 3 (run 38). Three repeats still gives a
standard deviation. Don't drop services.

### Decision rules (full list in `METHODOLOGY.md` §9)

**Dollars:** one figure → that. A range plus a stated single figure → the single
figure (and the range as low/high). A range only → type it as `50-500` (midpoint is
recorded). Several scenarios → "most likely"/"typical", else the lowest. Monthly
→ ×12. No number → `R`. Illustrative or hypothetical figures aren't the estimate.
Use the stated one and note `illustrative $X`. Same note every time for the $0
pattern: `$0 direct; risk unquantified`.

**Grade:** one letter → that. Two letters (C/D) → the **lower-risk** one, noted.
D+ → D, noted. No grade → blank.

## Step 4 — Push and hand back to Claude

```powershell
git add data/llm_run_log.xlsx data/responses METHODOLOGY.md
git commit -m "v2 runs complete"
git push
```

Then tell Claude: **"v2 runs are done and pushed."** Claude will audit every row
against the saved answers, run the analysis, finish the write-up, convert it for
the report, and make the clean handoff workbook.

## Step 5 — The team's figures

The team's six dollar figures go in **Comparison** column D (Spearman for dollars
appears in B21). The grade comparison with ToS;DR fills itself in (B24).

## Step 6 — Hand off to the team

Two files: the workbook and the report section.
