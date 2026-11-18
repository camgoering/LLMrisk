# LLM Risk Estimation — Prompts

**Owner:** Camden Goering · **Version:** 2.0 · **Last updated:** 2026-11-18

Version 2.0 adds a **risk grade (A–E)** to both prompts, so the model's grade can be
compared with the ToS;DR grade, and a **sources line** to P2. Version 1.0 (no grade)
was run once for P1 on 2026-11-12 and is kept as a pilot: see `PROMPTS_v1.md` and
`data/archive/`. Runs under different versions are never pooled.

Each prompt is reproduced here **verbatim**. Copy from this file (or use the files
`make_runs.py` builds) rather than retyping, because a changed word is a changed
condition. Never edit a version that has been run; add a new version instead.

Placeholders in `{{BRACES}}` are filled from `data/llm_run_log.xlsx` → `Profiles`.

**The prompts never mention ToS;DR.** The grade scale is defined neutrally (A =
lowest risk, E = highest) so that any mention of ToS;DR in a response comes from the
model itself. That mention is what the `Cites ToS;DR` column records.

---

## P1 — Naive

Tests what an ordinary user would actually get. Deliberately unengineered: the
original one-sentence question plus one sentence asking for a grade, with the policy
pasted underneath and no output format requested. Expect prose, hedging and ranges.
**All of that is data**, not failure.

```
What's the risk of accepting this privacy policy in terms of a specific yearly dollar amount? Also give it a risk grade from A (lowest risk) to E (highest risk).

{{POLICY_TEXT}}
```

---

## P2 — Profiled

Supplies the same inputs our own calculation takes, so the two numbers are
comparable, and requests a fixed output format so transcription is reliable.

```
You are estimating the financial risk to one individual of accepting a privacy policy.

User profile:
- Annual income: {{INCOME}} USD
- Credit score tier: {{CREDIT_TIER}}
- Available credit: {{CREDIT_LIMIT}} USD
- Savings: {{SAVINGS}} USD

Using the privacy policy below, estimate the expected cost to this user over the
next 12 months from identity theft or fraud enabled by data this service collects,
accounting for the chance that such an event occurs at all. Also grade the overall
risk of accepting this policy from A (lowest risk) to E (highest risk).

Reply with exactly these seven lines and nothing else:

ANNUAL_RISK_USD: <single number, no range, no currency symbol>
LOW_USD: <single number>
HIGH_USD: <single number>
RISK_GRADE: <one letter, A to E>
TOP_DATA_TYPES: <up to three, comma separated>
SOURCES: <any outside sources you relied on besides this policy, or none>
ONE_SENTENCE_BASIS: <one sentence>

Privacy policy:
{{POLICY_TEXT}}
```

---

## P3 — Decomposed (secondary, run only if time allows)

Unchanged from version 1.0 apart from the version number; see `PROMPTS_v1.md`. Not
part of the Tier 1 schedule.

```
You are estimating the financial risk to one individual of accepting a privacy policy.

User profile:
- Annual income: {{INCOME}} USD
- Credit score tier: {{CREDIT_TIER}}
- Available credit: {{CREDIT_LIMIT}} USD
- Savings: {{SAVINGS}} USD

Using the privacy policy below, estimate the expected 12-month cost to this user,
and show your decomposition.

Reply with exactly these six lines and nothing else:

P_BREACH_PER_YEAR: <decimal 0-1>
P_IDENTITY_THEFT_GIVEN_BREACH: <decimal 0-1>
IMPACT_IF_OCCURS_USD: <single number>
ANNUAL_RISK_USD: <single number>
DATA_TYPES_DRIVING_ESTIMATE: <up to three, comma separated>
ONE_SENTENCE_BASIS: <one sentence>

Privacy policy:
{{POLICY_TEXT}}
```

---

## Why two conditions

P1 alone gives ecological validity but messy output. P2 alone gives clean data about
a workflow no real user would follow. Running both shows the gap between them:
*does asking carefully change the answer, and by how much?* The grade adds a second
output that can be checked against an independent reference (ToS;DR) without any
dollar conversion.
