# LLM risk estimation — draft report section

*Draft for the team's workshop-paper report. Everything in `[brackets]` is filled in
after collection; do not fill any of it before the runs are done. Section headings
follow the team outline (Methods / Results / Discussion / Limitations). Cut freely —
this is written long so there is something to cut.*

---

## Methods: LLM risk elicitation

To test whether a large language model can stand in for our calculation, we asked
one publicly available chat model to estimate the annual dollar risk of accepting
each service's privacy policy, and repeated each request enough times to measure
how stable its answers are.

**Model and interface.** All runs used [product, model version as displayed] through
its standard web interface on a [tier] account, between [start date] and [end date].
We used the web interface rather than an API deliberately: it is what a consumer
would use, and it applies the provider's default sampling settings. The interface
does not expose temperature, system prompt or seed, so these were not controlled.
Web browsing was disabled for every run.

**Policies.** Six services spanning our exposure range were used: PayPal, X, Google
(ToS;DR grade E), Netflix (D), ChatGPT and LinkedIn (C). Each policy was saved once
as plain text on 2026-11-11 and the same snapshot was used for every run, so the
input did not change during collection. Sections applying only to non-US
jurisdictions were removed where a policy included them inline (PayPal's UK/EEA,
Mexico and Singapore disclosures); otherwise policies were used in full, between
29,000 and 77,000 characters. [If the paste test forced a cutoff: state it here.]

**Prompt conditions.** Each policy was presented under two prompts, reproduced in
full in Appendix [X]:

- **P1 (naive)** — a single question, as an ordinary user might ask it: *"What's
  the risk of accepting this privacy policy in terms of a specific yearly dollar
  amount?"* followed by the policy text. No output format was requested.
- **P2 (profiled)** — supplied the same user inputs our calculation takes (income,
  credit tier, available credit, savings, set to US averages; see §[profiles]),
  asked for the expected 12-month cost from identity theft or fraud enabled by the
  service's data, accounting for the probability that it occurs, and required a
  fixed five-line answer containing a point estimate, a low and high bound, the
  data types driving the estimate, and a one-sentence justification.

The contrast tests whether the number a user receives depends on how carefully the
question is asked.

**Profiles.** P2 used a single synthetic profile set to published US averages
([sources]). No participant data was ever sent to the model (see Ethics).

**Procedure.** Every run used a new chat, so no earlier answer could influence a
later one. The prompt and policy were pasted as one message and only the first
response was recorded: responses were never regenerated, followed up or rephrased.
Runs were collected in five rounds, each covering all six services under P1 and
then P2, so that any unannounced model update during collection would affect all
services equally rather than whichever service happened to be running. Two
calibration runs on PayPal checked the workflow beforehand and were excluded from
analysis. In total there were [60] scored runs.

**Coding responses.** Rules for turning responses into numbers were fixed before
collection began, so that how an awkward response was handled could not depend on
the number it contained. A single figure was recorded as given. A range with no
point estimate was recorded at its midpoint. Where several scenarios were given, we
took the one described as most likely, or the lowest if none was. Monthly or
lifetime figures were converted to annual. A response with no dollar figure was
recorded as a refusal. Refusals are reported as a result, not discarded.

**Measures.** For each service and prompt we report the mean and standard deviation
of the annual figure, and the coefficient of variation (CV = SD / mean) as a
scale-free measure of how reproducible the estimate is; we treat CV > 0.5 as
indicating the figure is not reproducible at the level of a dollar amount. We report
refusal rate per prompt. Because neither the model's figure nor ours has ground
truth, our main comparison is of *ordering* rather than magnitude: Spearman's rank
correlation between the services ordered by mean LLM estimate and ordered by our
calculated risk. We also report the correlation between the P1 and P2 orderings.

---

## Results: LLM estimates

**Table [N].** Annual risk estimates by service and prompt (scored runs only).

| Service | Prompt | n | Mean (USD) | SD (USD) | CV | Min – Max | Refused |
|---|---|---|---|---|---|---|---|
| PayPal | P1 | | | | | | /5 |
| PayPal | P2 | | | | | | /5 |
| X | P1 | | | | | | /5 |
| … | | | | | | | |

*(Source: `data/summary.csv` from `analyze.py`.)*

**Stability.** [Range of CV under P1 and under P2. How many of the twelve cells
exceed 0.5. Whether P2's fixed format reduced variability relative to P1.]

**Refusals.** [Refusal rate under P1 vs P2. What refusals looked like — e.g. a
qualitative risk description with no number, or a statement that it cannot
estimate.]

**Effect of prompt.** [Ratio of P2 to P1 means per service. Spearman's rho between
P1 and P2 orderings: high rho means phrasing moved magnitude but not order.]

**Agreement with our calculation.** [Spearman's rho, LLM P2 vs team, n = 6, exact
p. Table [N+1] with the two orderings side by side. With six services, rho must be
at least about 0.89 to reach p < .05, so report rho as descriptive unless it clears
that bar.]

**What the model attended to.** [From P2's TOP_DATA_TYPES field: which data types
it named most often per service, and whether they correspond to the categories our
calculation weights.]

---

## Discussion

*Write after results. Points to cover, in whichever direction the data falls:*

- **Reproducibility.** If CVs are high, a user asking the same question twice gets
  materially different answers, which limits an LLM's usefulness as a risk tool no
  matter how good its average is. If CVs are low, the model is at least consistent,
  and the question becomes whether it is consistent with anything else.
- **Prompt sensitivity.** If P1 and P2 diverge, the answer an ordinary user gets
  depends on prompting skill they do not have. If they agree, the naive workflow is
  more defensible than expected.
- **Ordering vs magnitude.** Agreement in ranking with our model is a claim that
  survives the absence of ground truth; agreement in dollar figures is not. If the
  orderings agree but magnitudes differ, both approaches may be tracking the same
  underlying signal (how much sensitive data a service holds) at different scales.
- **Refusals as a design feature.** A model that declines to give a number may be
  behaving more responsibly than one that produces a confident figure.

---

## Limitations

*Specific to this portion. Keep both kinds the course asks for: constraints of a
class project, and limits that would remain with more resources.*

- **No ground truth.** No published source gives the true annual dollar risk of
  accepting a privacy policy. We can measure the model's consistency and its
  agreement with our calculation, but neither establishes that either is correct.
- **One model, one interface.** Results describe [model] as served through its web
  interface during [dates], not LLMs in general. The provider may update the model
  without notice; rounds spread this across services but cannot remove it.
- **Uncontrolled sampling.** Temperature, system prompt and seed are not exposed by
  the web interface, so variability cannot be split into sampling and prompt
  effects.
- **Long inputs.** Policies of 29k–77k characters are long for a single message;
  models are known to weigh content unevenly across long inputs, so clauses deep in
  a policy may influence the estimate less than early ones.
- **Small n.** Five repeats per cell gives a usable but imprecise standard
  deviation, and six services gives little power for a rank correlation.
- **Manual transcription.** Figures were copied by hand; every logged figure can be
  checked against the full response text kept in the run log.
- **One synthetic profile.** P2 used US averages only, so we cannot say whether the
  model's estimate responds to the user's circumstances.
- **Policy preparation.** Regional sections were trimmed from one policy only
  (PayPal), because it was the only one that included them inline; this was applied
  by rule but is a judgement call.

---

## Ethics

We deliberately sent no participant data to the model. Every P2 run used a synthetic
profile of published US averages. Our survey promises anonymity, and transmitting
participants' income, savings or credit details to a third-party AI service would
have broken that promise. This points to a limitation of the approach itself, not
just our study: a real user who wanted a personalised estimate would have to
disclose exactly the financial details that make them a target, spending privacy to
measure privacy risk.

---

## Appendix: prompts

Paste the P1 and P2 blocks from `prompts/PROMPTS.md` verbatim (version 1.0).
