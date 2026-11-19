# Methodology — LLM Risk Estimation

**Purpose:** produce LLM-generated annual dollar risk estimates per service, with
enough repeats to report means and standard deviations, in a form directly
comparable to the team's own risk calculation.

---

## 1. Model and access

| Field | Value |
|---|---|
| Interface | Web UI (chat), not API |
| Provider / product | OpenAI ChatGPT |
| Model version string | GPT-6 (as displayed in the interface) |
| Account tier | Plus (paid) |
| Dates of data collection | v2.0 (main): *fill in* · v1.0 pilot (P1 only): 2026-11-12 |

The web interface does not expose temperature, system prompt, or seed. Run-to-run
variation therefore reflects whatever default sampling the provider applies, which
is also what a real user experiences. We treat this as ecologically appropriate and
report it as a limitation (§7).

Account settings for the whole collection period: Memory off, "Reference chat
history" off, custom instructions blank (or use Temporary Chat for every run).

## 2. Policy snapshots

Policies change. Every run must use a frozen copy, not a live page.

1. Run `fetch_policies.py` once, at the start of collection. It reads the URL list,
   downloads each policy, strips markup, and writes `policies/<service>_<YYYY-MM-DD>.txt`
   along with `policies/manifest.csv` recording URL, fetch timestamp, and character count.
   Snapshots were fetched on 2026-11-11. PayPal returned 403 to the script and was
   saved manually from a browser.
2. Use those files for every run. Do not let the model browse to a URL — browsing
   makes the input uncontrolled and may retrieve a different regional variant.
   **Paste, not upload.** The team brief suggested uploading the policy file. We
   paste the text into the message instead: an uploaded file may be searched in
   pieces rather than read in full, and how the interface handles uploads is not
   visible to the user, so pasting gives a more controlled, inspectable input.
   Decided with the group before collection.
3. **Full text, US sections only.** Each run uses the full snapshot, excluding
   sections that apply only to non-US jurisdictions in regionally segmented policies
   (see §9). Of the Tier 1 services only PayPal includes such sections inline; its
   UK/EEA, Mexico and Singapore disclosures were removed, giving
   `policies/PayPal_2026-11-11_US.txt` (76,988 characters of policy text, from 119,803). LinkedIn and
   ChatGPT link out to separate regional documents, which were not fetched. The
   original PayPal snapshot is kept unchanged alongside the trimmed one.
4. **Paste test = calibration.** PayPal is the longest Tier 1 input, so the two
   PayPal calibration runs (§5) double as the paste test. If they are accepted as
   one message, every Tier 1 input fits: no truncation is applied and
   `Truncated = N` on every run. If the interface rejects the message, the cutoff
   is set to the largest length that is accepted, applied identically to every
   service, `Truncated = Y` recorded for each run whose input exceeded it, and the
   calibration repeated. This is decided once, before any scored run, and not
   revisited.

**Known issues in the inherited URL list — resolve before fetching:**

- **Canvas** points at `instructure.com/policies/marketing-privacy`, which is
  Instructure's *marketing* privacy policy, not the Canvas LMS product policy.
- **Shopify** points at `shopify.com/legal/cookies`, a cookie policy rather than the
  main privacy policy.
- **Meta** points at an `mbasic.facebook.com` printable version pinned to a specific
  version id.
- **Claude, Truist, Epic Systems** have no usable privacy-document claims in the
  ToS;DR dataset and are excluded from this portion.

## 3. Profiles

P2 uses one profile (`US_AVG` row of the `Profiles` sheet): income, credit tier,
available credit, savings, each with its source in column F. The values must be the
same ones the team's own calculation uses, or the comparison does not hold.

**Values used (v2.0):** group means of the team survey responses: income
$19,000 (mean yearly income, including $0 answers), savings $21,000, credit tier
Good (mean of answered credit scores, 694; FICO Good = 670–739), available credit
$1,000 (team's band table for Good). The team's calculation uses the same inputs.

**No individual participant data is ever sent to the model.** The survey promises
anonymity, and transmitting a participant's financial details to a third-party
service would break that promise. If profile values are derived from the survey,
they are group-level figures. With only five responses, a median *is* one person's
answer, so use the team's US-average defaults or a rounded mean instead. State this
in the ethics section: it turns a limitation into a design decision.

## 4. Run matrix

**Tier 1 (required) — 60 runs.** Six services spanning the exposure range, two
prompt conditions, five repeats:

| Service | ToS;DR | Role in the spread |
|---|---|---|
| PayPal | E | highest financial-data exposure |
| X | E | high behavioral exposure |
| Google | E | high breadth |
| ChatGPT | C | AI service, mid |
| Netflix | D | low-mid |
| LinkedIn | C | lowest in our exposure scoring |

**Prompt version.** Main collection uses prompts v2.0 (`prompts/PROMPTS.md`), which
add an A–E risk grade to both prompts and a sources line to P2. A complete P1 run
under v1.0 (no grade question; 2026-11-12) is kept as a **pilot** in
`data/archive/`. It is never pooled with v2.0, but comparing pilot P1 with v2.0 P1
shows whether adding the grade question moved the dollar figures.

**Tier 2 (if time) —** the remaining seven services, P2 only, three repeats each.

**Tier 3 (if time) —** P3 on two services, three repeats, reported qualitatively.

Five repeats is the minimum that gives a usable standard deviation. If you can only
do three for some services, record the n and report it per cell — do not average
across different n silently.

## 5. Procedure — follow exactly

For every single run:

1. **Open a brand-new chat.** Never reuse one. Prior turns contaminate the next
   estimate and destroy independence between repeats. This is the easiest rule to
   break and the most damaging.
2. Open the run's file in `runs/` (generated by `make_runs.py` from
   `prompts/PROMPTS.md`, the Profiles sheet and the policy snapshot), select all,
   copy, and paste it as one message. The file is the prompt verbatim with the
   placeholders and policy text already filled in, so nothing is retyped.
3. Use a **Temporary Chat** (or have Memory, "Reference chat history" and custom
   instructions all switched off for the whole collection period), so no saved
   context from earlier runs or other conversations reaches the model. Do not
   enable web search. If a response cites web sources anyway, note `searched` in
   Notes.
4. Send. **Take the first response only.** Never regenerate, never follow up, never
   nudge toward a number.
5. Record the result (normally via `log_run.py`, which copies the prompt to the
   clipboard, reads the answer back from it, and writes the row; it never contacts
   the model) in `data/llm_run_log.xlsx` → `Run Log`, including `Round` and
   `Calibration`, applying the decision rules in §9.
6. If the model declines to give a figure, hedges without a number, or answers that
   it cannot estimate: record `Refused = Y`, leave the dollar fields blank, and paste
   what it said into `Raw Response`. **Refusals are a result.** The refusal rate per
   condition goes in the paper.
7. Close the chat.

One run per row. Fill `Run ID` sequentially so nothing is silently overwritten.

### Order of runs

- **Calibration first.** Two PayPal runs (run 1 = P1, run 2 = P2) confirm the
  workflow end to end: input accepted, output parseable, logging works. They are
  logged with `Calibration = Y`, Round 0, and excluded from every statistic. Prompts
  are not revised after calibration unless the output is unusable; any revision
  becomes a new version and the calibration is repeated.
- **Rounds, P1 and P2 interleaved.** One round = all six Tier 1 services under P1,
  then the same six under P2 (twelve runs). Five rounds. Record the round number in
  `Round`. If the provider updates the model mid-collection, rounds spread the drift
  evenly across services *and* prompts instead of confounding it with whichever
  service or prompt was running at the time. (`make_runs.py --order blocks` exists
  for the case where P1 must start before the profile is available; using it is a
  deviation and must be recorded here.)
- Service order within a round is fixed: PayPal, X, Google, ChatGPT, Netflix,
  LinkedIn. The full schedule is generated by `make_runs.py` (`runs/SCHEDULE.csv`).
- After round 1, check the Summary sheet for problems with the *procedure* (e.g.
  unparseable output). Do not change anything in response to the *values*.

## 6. Analysis

The `Summary` sheet computes n, mean, standard deviation, coefficient of variation,
min and max per service × prompt automatically as rows are added, excluding rows
with `Calibration = Y`. The `Comparison` sheet computes Spearman's rho between the
LLM's P2 ranking and the team's ranking once the team's figures are typed in.

`analyze.py` reads the Run Log directly and produces the same table as CSV, plus
Spearman's rho for P1 vs P2 and for each prompt vs the team's figures.

Report at minimum:

- Mean and SD of `ANNUAL_RISK_USD` per service, per prompt condition
- **Coefficient of variation** (SD / mean) — the headline stability number. A CV
  above ~0.5 means the model's estimate is not reproducible at the level of a dollar
  figure, which is itself a substantive finding about LLMs as a risk tool.
- Refusal rate per condition
- Spearman correlation between the LLM's service ranking and the team's ranking.
  Comparing *rankings* is far more robust than comparing point estimates, and it
  survives the objection that neither dollar figure has ground truth.
- **Risk grade (v2.0):** grade distribution and mean grade (A = 1 … E = 5) per
  service × prompt; exact-match and within-one-letter agreement with the ToS;DR
  grade; Spearman between the LLM's mean grade and the ToS;DR grade (six services,
  with ties in ToS;DR: E, E, E, D, C, C).
- **ToS;DR as a source (v2.0):** share of responses per prompt that mention ToS;DR.
  The prompts never mention it and browsing is off, so a mention comes from the
  model's training data. Compare grades in runs that cite ToS;DR with those that do
  not: if citing runs match ToS;DR far more often, the model's grade may be recalled
  rather than judged from the policy.
- **Internal consistency (v2.0):** run-level Spearman between the dollar figure and
  the grade. A model whose E grades come with small dollar figures is not using one
  coherent notion of risk.

The `Summary` and `Comparison` sheets compute the grade counts, mean grade, ToS;DR
mention rate and grade-vs-ToS;DR Spearman; `analyze.py` adds agreement rates, the
consistency check and `data/grades.csv`.

## 7. Limitations specific to this portion

- **No parameter control.** Temperature, system prompt and seed are not exposed by
  the web interface. Variance cannot be decomposed into sampling versus prompt
  effects.
- **Non-stationary model.** The provider may update the model mid-collection without
  notice. Collect in as narrow a window as possible and record dates per run.
- **No ground truth for dollars.** No published source gives the true annual dollar
  risk of accepting a given privacy policy. We can measure the model's *consistency*
  and its *agreement with our model*, but neither establishes correctness. This bounds
  every claim in this section.
- **Manual transcription.** Figures are read off by hand; transcription error is
  possible. Mitigation: `Raw Response` retains the model's text so any cell can be
  re-checked against it.
- **Long inputs.** Tier 1 inputs run from ~29k to ~78k characters. Even when the
  full text is accepted, models are known to attend unevenly across long inputs, so
  clauses deep in a long policy may carry less weight than early ones. If the paste
  test forces a cutoff (§2.4), late clauses are not seen at all.
- **Regional trimming.** Only PayPal's inline non-US sections were removed. Policies
  that link out to separate regional documents were used as fetched, so the rule
  removes text from one service only. Applied consistently, but it is a judgement
  call and is reported as such.
- **Single provider.** Tier 1 uses one model. Results describe that model, not LLMs
  generally.
- **Privacy cost of the workflow itself.** A user who actually wanted this estimate
  would have to send their income, savings and credit details to a third party —
  spending privacy to measure privacy risk. We avoided this with synthetic profiles,
  but a real deployment could not.

## 8. Files

```
├── METHODOLOGY.md              this file
├── prompts/PROMPTS.md          verbatim prompt text, versioned
├── fetch_policies.py           one-time policy snapshot downloader (already run)
├── make_runs.py                builds paste-ready run files + schedule
├── analyze.py                  summary, rankings and Spearman from the run log
├── policies/                   dated snapshots + manifest.csv
├── runs/                       generated by make_runs.py — one file per run
├── data/llm_run_log.xlsx       run log, profiles, auto-computed summary
├── writeup/llm_section.md      draft of this portion of the report
└── reference/                  team documents (survey, data matrix, notes)
```

## 9. Decision rules (fixed before collection)

These are fixed before any output is seen, so that the handling of an awkward
response cannot be influenced by what number it contains.

- **Single dollar figure** → record as `Annual Risk USD`.
- **Range with no point estimate** → endpoints into `Low USD` / `High USD`, midpoint
  into `Annual Risk USD`, note `midpoint` in Notes.
- **Several scenario figures** → take the one described as most likely or typical;
  if none is, take the lowest and note it.
- **No number at all** → `Refused = Y`, dollar fields blank, full text in
  `Raw Response`.
- **Monthly or lifetime figure** → convert to annual and note the conversion.
- **P2/P3 format not followed but a figure is given** → apply the rules above to the
  prose; note `format not followed`.
- **Never** regenerate, follow up, or rephrase to get a number.

**Risk grade (v2.0):**

- One letter A–E → record it.
- Two letters with no single choice (e.g. "C/D", "C–D") → record the lower-risk
  letter and note `several grades mentioned`. (This mirrors the "take the lowest"
  rule for dollar scenarios.)
- Plus/minus (e.g. "D+") → record the letter only; note it.
- No grade at all → leave blank and note `no grade`. This is separate from a dollar
  refusal: a run can have a figure and no grade, or a grade and no figure.

**Cites ToS;DR (v2.0):** `Y` if the response names ToS;DR, "Terms of Service; Didn't
Read" or tosdr.org anywhere, in any spelling; otherwise `N`. `log_run.py` detects
this automatically and shows the passage for confirmation. For P2, the model's
`SOURCES:` line is recorded verbatim in `Sources (P2)`.

**Policy text rule:** use the full policy text, excluding sections that apply only to
non-US jurisdictions in regionally segmented policies. Nav menus and site footers
from manual saves are left in place. Applied identically to every service.
