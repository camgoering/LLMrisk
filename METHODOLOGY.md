# Methodology — LLM Risk Estimation

**Purpose:** produce LLM-generated annual dollar risk estimates per service, with
enough repeats to report means and standard deviations, in a form directly
comparable to the team's own risk calculation.

---

## 1. Model and access

| Field | Value |
|---|---|
| Interface | Web UI (chat), not API |
| Provider / product | *record exactly, e.g. ChatGPT, GPT-5.1* |
| Model version string | *record what the UI displays; screenshot it once* |
| Account tier | *free / Plus / Team* |
| Dates of data collection | *fill in* |

The web interface does not expose temperature, system prompt, or seed. Run-to-run
variation therefore reflects whatever default sampling the provider applies, which
is also what a real user experiences. We treat this as ecologically appropriate and
report it as a limitation (§7).

## 2. Policy snapshots

Policies change. Every run must use a frozen copy, not a live page.

1. Run `fetch_policies.py` once, at the start of collection. It reads the URL list,
   downloads each policy, strips markup, and writes `policies/<service>_<YYYY-MM-DD>.txt`
   along with `policies/manifest.csv` recording URL, fetch timestamp, and character count.
2. Use those files for every run. Do not let the model browse to a URL — browsing
   makes the input uncontrolled and may retrieve a different regional variant.
3. If a policy is too long for one message, paste the first 12,000 characters and
   record `Truncated = Y` in the run log. Apply the same cutoff to every service.

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

All profiles are **synthetic**, set to published US averages. Values and sources
live in the `Profiles` sheet of `data/llm_run_log.xlsx` and come from Jules's source
research — fill them there, not here, so there is one authority for each figure.

No real participant data is ever sent to the model. This is deliberate: the survey
promises anonymity, and transmitting participant financial details to a third-party
service would break that promise. State this explicitly in the paper's ethics
section — it converts a limitation the team identified into a design decision.

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
2. Paste the prompt verbatim from `prompts/PROMPTS.md`, with placeholders filled
   from the Profiles sheet.
3. Paste the policy snapshot text where indicated.
4. Send. **Take the first response only.** Never regenerate, never follow up, never
   nudge toward a number.
5. Record the result in `data/llm_run_log.xlsx` → `Run Log`.
6. If the model declines to give a figure, hedges without a number, or answers that
   it cannot estimate: record `Refused = Y`, leave the dollar fields blank, and paste
   what it said into `Raw Response`. **Refusals are a result.** The refusal rate per
   condition goes in the paper.
7. Close the chat.

One run per row. Fill `Run ID` sequentially so nothing is silently overwritten.

## 6. Analysis

The `Summary` sheet computes n, mean, standard deviation, coefficient of variation,
min and max per service × prompt automatically as rows are added. Nothing to run.

`analyze.py` is optional and produces the same table as CSV plus a
comparison-ready column for the team's own calculation.

Report at minimum:

- Mean and SD of `ANNUAL_RISK_USD` per service, per prompt condition
- **Coefficient of variation** (SD / mean) — the headline stability number. A CV
  above ~0.5 means the model's estimate is not reproducible at the level of a dollar
  figure, which is itself a substantive finding about LLMs as a risk tool.
- Refusal rate per condition
- Spearman correlation between the LLM's service ranking and the team's ranking.
  Comparing *rankings* is far more robust than comparing point estimates, and it
  survives the objection that neither dollar figure has ground truth.

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
- **Truncation.** Long policies are cut at a fixed character count, so the model may
  not see clauses that appear late in the document.
- **Single provider.** Tier 1 uses one model. Results describe that model, not LLMs
  generally.
- **Privacy cost of the workflow itself.** A user who actually wanted this estimate
  would have to send their income, savings and credit details to a third party —
  spending privacy to measure privacy risk. We avoided this with synthetic profiles,
  but a real deployment could not.

## 8. Files

```
llm-risk/
├── METHODOLOGY.md              this file
├── prompts/PROMPTS.md          verbatim prompt text, versioned
├── fetch_policies.py           one-time policy snapshot downloader
├── analyze.py                  optional summary + comparison table
├── policies/                   dated snapshots + manifest.csv  (generated)
└── data/llm_run_log.xlsx       run log, profiles, auto-computed summary
```

## 9. Decision rules

If the response gives a single dollar figure, record it as ANNUAL_RISK_USD.
If it gives a range with no point estimate, record the endpoints as LOW_USD and HIGH_USD and the midpoint as ANNUAL_RISK_USD. Note midpoint in Notes.
If it gives several figures for different scenarios, take the one described as most likely or typical. If none is, take the lowest and note it.
If it gives no number at all, Refused = Y, dollar fields blank, full text in Raw Response.
If it gives a monthly or lifetime figure, convert to annual and note the conversion.
Never regenerate, never follow up, never rephrase to get a number.
Policy text rule: use the full policy text, excluding sections that apply only to non-US jurisdictions in regionally segmented policies. Nav menus and site footers from manual saves are left in place. Applied identically to every service.