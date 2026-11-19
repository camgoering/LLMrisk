# LLM Risk Estimation

## Methods

We asked ChatGPT (web interface, model shown as GPT-6, paid Plus account) to
estimate the yearly dollar risk of accepting the privacy policies of six services:
PayPal, X, Google, ChatGPT, Netflix and LinkedIn. Each policy was saved once as text
(2026-11-11) and pasted in full into the chat, so every run saw identical input.
Sections that applied only to other countries were removed (PayPal only). Web search
was off.

We used two prompts:

- **P1 (naive):** the question an ordinary user would ask: *"What's the risk of
  accepting this privacy policy in terms of a specific yearly dollar amount? Also
  give it a risk grade from A (lowest risk) to E (highest risk)."*
- **P2 (profiled):** gave the same inputs as our risk model (income $19,000, credit
  tier Good, available credit $1,000, savings $21,000, all group means from our
  survey) and asked for the expected 12-month cost from identity theft or fraud,
  plus a low/high range, an A–E grade, the top data types and any outside sources,
  in a fixed format.

Neither prompt mentions ToS;DR, so any mention of it would come from the model
itself.

Each service was run 5 times under each prompt: 60 scored runs, plus 2 calibration
runs that were not counted. Every run used a new chat, and only the first answer
was recorded, with no regenerating or follow-up questions. Runs were done in five
rounds (all six services under P1, then under P2) so that a model update
mid-collection would affect every service equally. Rules for turning answers into
numbers (single figure, range, several scenarios, no number) were fixed before
collection. All runs were collected on 2026-11-18.

We report the mean and coefficient of variation (CV = SD ÷ mean; above 0.5 means the
figure is not reproducible) per service and prompt, refusals, the grade compared
with the ToS;DR grade, and Spearman's ρ between rankings. With six services, ρ must
be at least 0.89 to reach p < .05, so ρ values are descriptive.

## Results

| Service | ToS;DR | P1 mean $/yr | P1 CV | P1 grades | P2 mean $/yr | P2 CV | P2 grades |
|---|---|---|---|---|---|---|---|
| PayPal | E | 21.2 | 0.35 | DDDDD | 2.8 | 0.47 | CCCCC |
| X | E | 50.0 | 0.00 | DDDDD | 2.2 | 0.75 | BCBCC |
| Google | E | 45.0 | 0.67 | DCCDC | 3.2 | 0.51 | BBBCB |
| ChatGPT | C | 13.0 | 0.52 | CCCCC | 1.0 | 0.00 | BCBBB |
| Netflix | D | 19.2 | 0.39 | CCCCC | 1.2 | 0.37 | BBBBB |
| LinkedIn | C | 40.0 | 0.34 | DDDDD | 4.4 | 0.30 | BBBBB |

*P1 had two refusals (one Google, one PayPal), so those means are over four runs.*

**Asking carefully made the risk look smaller.** P2's estimates were 8 to 23 times
lower than P1's ($1–$4 versus $13–$50 a year), and P2's grades were about one
letter better (mostly B/C versus C/D).

**The figures were round numbers, not calculations.** 25 of 28 P1 figures were
exactly $10, $25, $50 or $60, and 29 of 30 P2 figures were $1, $2 or $5. Four of the
twelve service/prompt combinations had a CV above 0.5. Where the CV was low, it was
because the same round number repeated (X under P1 was $50 every time).

**The model gave numbers but disowned them.** Every P1 answer said its figure was
not a measured or predicted loss, and 20 of 30 framed it as a "personal decision
benchmark", meaning what the user might pay to avoid the trade-off, not as an
expected cost. Two P1 answers (7%) gave no figure at all. P2 never refused.

**Grades vs ToS;DR.** The ordering roughly followed ToS;DR (ρ = 0.70 for P2, 0.38
for P1), but exact matches were rare (6 of 60), and the model **never gave an E**,
while ToS;DR gives three of these services an E.

**ToS;DR was never cited.** None of the 60 answers mentioned ToS;DR, and every P2
answer listed its sources as "none", so the grades were not copied from ToS;DR.

**Consistency.** Under P1, higher grades came with higher dollar figures (run-level
ρ = 0.61, p ≈ .001). Under P2 the link was weak (ρ = 0.21). The prompt also changed
the ranking of services (P1 vs P2 ρ = 0.60).

**Agreement with our model:** Spearman ρ between the LLM's P2 ranking and our
calculated ranking = [ρ] (from the Comparison sheet).

**Pilot.** An earlier P1 run without the grade question (2026-11-12) gave higher
figures for some services (Google $100, ChatGPT $42), so even adding one sentence
to the prompt moved the dollar estimates.

## Discussion

An LLM will almost always produce a dollar figure for privacy risk, but the figure
depends on how the question is asked, repeats as a small set of round numbers, and
is described by the model itself as not a real estimate. Our model and the LLM use
different inputs: ours uses each company's breach history, while the LLM reads only
the policy. So disagreement between them is expected, and it doesn't mean either
one is simply wrong.

**Limitations:**
- No source gives the true dollar risk of accepting a policy, so we can measure
  consistency and agreement, not correctness.
- One model, used through its web interface. Settings like temperature can't be
  controlled, and the model can change without notice.
- ToS;DR grades rate a service's terms overall, not financial risk.
- Answers were coded by hand. Every logged figure was checked against the saved
  response, and three typing errors were corrected.

**Ethics:** no individual participant's data was sent to the model. P2 used one
group-level profile. A real user wanting a personal estimate would have to give an
AI company the financial details that make them a target.

## Appendix: prompts

**P1**
```
What's the risk of accepting this privacy policy in terms of a specific yearly dollar amount? Also give it a risk grade from A (lowest risk) to E (highest risk).

[policy text]
```

**P2**
```
You are estimating the financial risk to one individual of accepting a privacy policy.

User profile:
- Annual income: 19,000 USD
- Credit score tier: Good
- Available credit: 1,000 USD
- Savings: 21,000 USD

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
[policy text]
```
