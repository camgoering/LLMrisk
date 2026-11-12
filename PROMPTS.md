# LLM Risk Estimation — Prompts

**Owner:** Camden Goering · **Version:** 1.0 · **Last updated:** 2026-11-11

Three prompt conditions. Each is reproduced here **verbatim** — copy from this file
rather than retyping, because a changed word is a changed condition. If you revise a
prompt, add it as a new version (P2.1, etc.) and never edit one that has already been
run; runs under different wording are not comparable.

Placeholders in `{{BRACES}}` are filled from `data/llm_run_log.xlsx` → `Profiles` sheet.

---

## P1 — Naive

Tests what an ordinary user would actually get. Deliberately unengineered: one
sentence, policy pasted underneath, no output format requested. Expect prose,
hedging, ranges, and occasional refusals — **all of that is data**, not failure.

```
What's the risk of accepting this privacy policy in terms of a specific yearly dollar amount?

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
accounting for the chance that such an event occurs at all.

Reply with exactly these five lines and nothing else:

ANNUAL_RISK_USD: <single number, no range, no currency symbol>
LOW_USD: <single number>
HIGH_USD: <single number>
TOP_DATA_TYPES: <up to three, comma separated>
ONE_SENTENCE_BASIS: <one sentence>

Privacy policy:
{{POLICY_TEXT}}
```

---

## P3 — Decomposed (secondary, run only if time allows)

Asks the model to show the same decomposition our model uses. The point is not the
number — it is whether the model reasons in the same shape we do. Run on two
services only, three repeats each, and report qualitatively.

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

## Why three conditions

P1 alone gives ecological validity but unusable output. P2 alone gives clean data
about a workflow no real user would follow. Running both lets us report the gap
between them, which is a finding in its own right: *does asking carefully change the
answer, and by how much?*

If P1 and P2 produce similar figures, the model's estimate is insensitive to how it
is asked, and the naive workflow is defensible. If they diverge sharply, then the
number a real user would get depends on prompt skill they do not have — which is a
more interesting result and a direct limitation on LLMs as a consumer privacy tool.
