# CLAUDE.md — LLM Risk Estimation (Camden's portion)

Handoff context for a fresh session. Read this first; it is self-contained.

---

## 1. What this folder is

One person's contribution to a five-person term project in **COSC 469/569, Human
Factors in Cybersecurity**, University of Tennessee Knoxville, Fall 2026
(instructor: Dr. Doowon Kim).

**Camden Goering owns the LLM portion:** get a large language model to produce an
annual dollar risk estimate for accepting a given privacy policy, repeated enough
times to report means and standard deviations, in a form directly comparable to the
team's own calculated risk figure.

Repo: `github.com/frozensriracha/COSC469FinalProject`, folder `llm-risk/`.

## 2. Deadlines

| Date | What |
|---|---|
| Nov 17 / 19 / 24, 2026 | Final project presentations (live demo required) |
| Dec 1, 2026 | Final report due |

Today is Nov 12. Data collection is **not started**. Remaining work on this portion
is roughly two hours of runs plus the write-up.

## 3. The project, briefly

The team measures the financial risk a user takes on by accepting a service's
privacy policy, then compares their own calculated figure against what an LLM
produces for the same policy.

Central formula, from the team's planning doc:

```
RISK = IMPACT × PROBABILITY

IMPACT      = Available Credit + Savings + (hours lost to identity-theft recovery × hourly rate)
PROBABILITY = P(identity theft | breach) × P(breach) × P(any user involved)
              × P(covered data involved) × P(data used in identity theft)
```

Supporting data the team has already built:

- **ToS;DR claim verification** — ~710 claims across 16 services, each checked
  against live policy text, with ToS;DR severity (good / neutral / bad / blocker).
  349 of those are privacy-document claims.
- **Company data-type matrix** — 15 services × ~35 data types, marked Y / C / ~.
- **Breach history research** — Wyatt and Jeffery, in progress.
- **User survey** — built in Qualtrics by John.

### History worth knowing

The project pivoted several times: service-level exposure scoring → three-way
ranking comparison (user vs AI vs reference) → the current **monetary** framing.

**The monetary direction was decided by the team lead. Camden raised objections and
was overruled. Do not reopen that debate.** Help execute it well. The useful
contributions within that direction are: monetize at the service level rather than
asking participants their net worth, anchor every dollar figure to a published
source, and report a sensitivity analysis rather than a single point estimate.

## 4. What this portion delivers

1. A reproducible protocol for eliciting dollar risk estimates from an LLM
2. Logged runs with enough repeats for means and standard deviations
3. A comparison between the LLM's figures and the team's calculation
4. A written methodology section, including limitations

**The headline results to report:**

- Mean and SD of the annual figure per service, per prompt condition
- **Coefficient of variation (SD / mean)** — the key number. Above ~0.5 means the
  model's dollar estimates are not reproducible, which is a substantive finding
  either way it lands.
- Refusal rate per prompt condition
- **Spearman's rho between the LLM's ranking of services and the team's ranking.**
  This is the robust comparison — neither dollar figure has ground truth, so
  agreement in *ordering* is a claim that survives scrutiny where "our number vs
  their number" does not.

## 5. Current state

**Done**

- [x] Folder scaffold in the repo
- [x] Three prompt conditions written (`prompts/PROMPTS.md`)
- [x] Methodology / replication protocol drafted (`METHODOLOGY.md`)
- [x] Run-log workbook built with self-computing stats (`data/llm_run_log.xlsx`)
- [x] Policy snapshots fetched for all six Tier 1 services
- [x] PayPal non-US sections trimmed → `policies/PayPal_2026-11-11_US.txt`
- [x] Decision rules in `METHODOLOGY.md` §9; length rule (§2.3–2.4), rounds and
      calibration rules (§5) added
- [x] `Services` sheet filled; Run Log has `Round` and `Calibration` columns;
      Summary excludes calibration; Comparison computes Spearman (verified in LibreOffice)
- [x] `make_runs.py` builds paste-ready run files + `runs/SCHEDULE.csv`
- [x] `analyze.py` excludes calibration, computes rho vs team with exact p
- [x] Report section drafted (`writeup/llm_section.md`), results left blank

**Not done**

- [x] `Profiles` US_AVG filled with sourced figures (SSA AWI 2024, FICO 714 → Good,
      Experian $35,687, SCF 2022 median $8,000) — team must confirm it uses the same
- [x] `NEXT_STEPS.md` — the user's step-by-step guide for finishing; follow it
- [ ] Two calibration runs (double as the paste test for the 77k-char PayPal input)
- [ ] 60 Tier 1 runs
- [ ] Analysis and write-up

## 6. Files

| Path | What it is |
|---|---|
| `METHODOLOGY.md` | Replication protocol. The authority on how runs are done. |
| `prompts/PROMPTS.md` | Verbatim prompt text, three conditions, versioned. |
| `fetch_policies.py` | Already run. Downloads dated policy snapshots. |
| `make_runs.py` | Builds `runs/NNN_<prompt>_<service>.txt` + `runs/SCHEDULE.csv`. |
| `analyze.py` | Summary, refusal and ranking CSVs; Spearman with exact p. |
| `data/llm_run_log.xlsx` | Run log. Summary and Comparison sheets compute themselves. |
| `policies/` | Dated snapshots + `manifest.csv` (committed). |
| `writeup/llm_section.md` | Draft report section. |
| `reference/` | Team documents (survey, data-type matrix, claims verification, notes). |

### Workbook sheets

`README` (legend) · `Profiles` (synthetic user profiles) · `Services` ·
`Run Log` (one row per run; dropdowns on Prompt, Service, Refused, Truncated,
Calibration; Round 0 = calibration) ·
`Summary` (auto: n, mean, SD, CV, min, max, refusal rate per service × prompt) ·
`Comparison` (LLM P2 mean vs team figure; ranks among services with both figures,
ties averaged; Spearman's rho in B21).

Yellow cells are for typing in; blue cells are formulas. Verified working: three
runs of 4000/6000/8000 plus one refusal yields n=3, mean 6000, SD 2000, CV 0.33,
refusal rate 0.25, with a calibration row of 100000 correctly excluded.

## 7. Protocol rules that must not be broken

1. **A brand-new chat for every run.** Never reuse one — prior turns contaminate the
   next estimate and destroy independence between repeats.
2. **First response only.** Never regenerate, never nudge toward a number.
3. **A refusal is data.** `Refused = Y`, dollar fields blank, full text in
   `Raw Response`. Refusal rate goes in the paper.
4. **Paste the saved snapshot.** Never let the model browse to a URL — browsing makes
   the input uncontrolled and may fetch a different regional variant.
5. **Run in rounds, not blocks.** Round = all six services under P1, then all six
   under P2. Five rounds. If the provider updates the model mid-collection, rounds
   spread that drift evenly across services instead of confounding it with whichever
   service was being run at the time.

## 8. Decision rules — paste into METHODOLOGY.md before any runs

These must be fixed before seeing output, or the handling is contaminated by the data.

> **Decision rules (fixed before collection)**
>
> - Single dollar figure → record as `ANNUAL_RISK_USD`.
> - Range with no point estimate → endpoints into `LOW_USD` / `HIGH_USD`, midpoint
>   into `ANNUAL_RISK_USD`, note `midpoint` in Notes.
> - Several scenario figures → take the one described as most likely or typical; if
>   none is, take the lowest and note it.
> - No number at all → `Refused = Y`, dollar fields blank, full text in Raw Response.
> - Monthly or lifetime figure → convert to annual, note the conversion.
> - Never regenerate, never follow up, never rephrase to get a number.
>
> **Policy text rule:** use the full policy text, excluding sections that apply only
> to non-US jurisdictions in regionally segmented policies. Nav menus and footers
> from manual browser saves are left in place. Applied identically to every service.

## 9. Run matrix

**Tier 1 (required), 60 runs** — six services × two prompts (P1, P2) × five repeats:

| Service | ToS;DR | Snapshot chars | Note |
|---|---|---|---|
| PayPal | E | 121,026 | manual browser save (script got 403); trim non-US sections |
| X | E | 34,563 | |
| Google | E | 68,679 | |
| ChatGPT | C | 29,725 | |
| Netflix | D | 71,278 | |
| LinkedIn | C | 43,269 | |

**Tier 2 (if time)** — remaining services, P2 only, three repeats.
**Tier 3 (if time)** — P3 on two services, three repeats, reported qualitatively.

If time is short, cut repeats before cutting services. Six services × 2 prompts × 3
repeats still yields a standard deviation.

## 10. Known issues

### In this portion

- **Adobe, McDonald's, Uber** returned 403/406 (bot blocking); **Airbnb** returned
  200 but only 1,564 chars (JavaScript-rendered); **Meta's** URL is a version-pinned
  `mbasic.facebook.com` page that now 400s. All Tier 2 — fix by manual browser save
  if they're needed. Meta needs a working URL first.
- **Canvas** URL points at Instructure's *marketing* privacy policy, not the Canvas
  LMS product policy. **Shopify** URL points at a cookie policy, not the main privacy
  policy. Both inherited from the team's verification spreadsheet. Verify or note.
- **Claude, Truist, Epic Systems** excluded — no usable privacy-document claims in
  the ToS;DR dataset, so nothing to compare against.
- **No ground truth for dollars.** No published source gives the true annual dollar
  risk of accepting a policy. This bounds every claim in this section: consistency
  and agreement can be measured, correctness cannot.

### Elsewhere in the project — raised with the team, status unknown

Not Camden's to fix, but they affect how his results should be framed:

- **Breach probability formula is inverted.** The planning doc says
  `(current year − year of first breach) / total breaches`, which is years-per-breach
  and can exceed 1. Should be `breaches / years`.
- **Credit limit table is off by an order of magnitude** (Poor $0 / Fair $500 /
  Good $1000 / Excellent $1500) and has no cited source.
- **`Impact = Credit + Savings` assumes the consumer bears the loss.** US law largely
  does not: the Fair Credit Billing Act caps card-fraud liability at $50, and
  Regulation E caps electronic transfer losses similarly. The time-cost term is the
  component that survives this critique.
- **Five multiplied probabilities compound error badly,** and two of them —
  P(theft | breach) and P(data used in theft) — are near-duplicates, so the model
  discounts twice.
- **The data-type matrix has a fill-down artifact:** five rows (approximate location,
  usage/activity, device IP, crash/performance, cookies) are byte-identical across
  all fifteen services. ChatGPT's column is only 45% coded and shows blanks for
  device identifiers and cookies, which OpenAI's policy clearly covers. Under-coded
  services come out looking artificially safe.
- **Breach tracker (`reference/Company_Breach_Probability_Tracker.xlsx`, Wyatt &
  Jeffery).** Uses breaches / years, so the inverted-formula issue above is fixed
  there. But ChatGPT and Netflix have **zero qualifying breaches**, so P(breach) = 0
  and the team's risk for both is exactly $0 — a tie at the bottom of the team
  ranking, which weakens Spearman with n = 6. PayPal's one breach touched 0.008% of
  users, so the team will likely rank PayPal low; the LLM, which sees only the
  policy, will likely rank it high. The two methods take different inputs (breach
  history vs policy text) — frame any disagreement that way, not as one being wrong.
- **Two incompatible surveys exist:** a pre/post comparison instrument built in
  Qualtrics, and a different income/credit/savings instrument described in the
  planning doc. Unclear which is being used.

## 11. Do this next

Follow `NEXT_STEPS.md`. When the user says runs are done, start at its step 9.

## 12. Environment

Windows, PowerShell. `wc` is not available — use
`Get-ChildItem policies\*.txt | Select-Object Name, Length`.
Python is on PATH as `python`. `requests` and `beautifulsoup4` are installed.
No OpenAI API key — all runs are manual through the chat web interface, by choice.
