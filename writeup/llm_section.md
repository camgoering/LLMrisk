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

**Model and interface.** All runs used ChatGPT (model shown in the interface as
"GPT-6") through its standard web interface on a paid Plus account, between
2026-11-12 and [end date].
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
29,000 and 77,000 characters. The longest (PayPal) was accepted as a single message,
so no policy was truncated.

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
All P1 runs were collected on 2026-11-12 and all P2 runs on [date]. Within each day,
runs were collected in five rounds, each covering all six services, so that any
unannounced model update during collection would affect all services equally
rather than whichever service happened to be running. Because the two prompts were
run on different days, a model update between them cannot be separated from the
prompt effect; the model version shown in the interface was recorded on every run
[and did / did not change]. One calibration run on PayPal opened each day's block
and was excluded from analysis. In total there were [60] scored runs.

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

### P1: the naive question

**Table [N].** Annual risk estimates under P1 (naive prompt), 2026-11-12, five
scored runs per service (calibration run excluded).

| Service | ToS;DR | Mean (USD) | Median | SD | CV | Min – Max | Refused |
|---|---|---|---|---|---|---|---|
| Google | E | 100 | 100 | 0 | 0.00 | 100 – 100 | 0/5 |
| X | E | 53 | 50 | 35 | 0.66 | 15 – 100 | 0/5 |
| ChatGPT | C | 42 | 25 | 36 | 0.84 | 10 – 100 | 0/5 |
| LinkedIn | C | 35 | 25 | 14 | 0.39 | 25 – 50 | 0/5 |
| Netflix | D | 27 | 25 | 14 | 0.53 | 10 – 50 | 0/5 |
| PayPal | E | 25 | 25 | 18 | 0.71 | 0 – 50 | 0/5 |

*(Source: `data/summary.csv` from `analyze.py`; SD rounded to the nearest dollar.)*

**The model always gave a number, and always disowned it.** None of the 30 P1
responses was a refusal: each named a dollar figure. Yet every response (30/30)
described its figure as illustrative, 27 stated explicitly that it was not a
defensible, measured, actuarial or statistically established estimate, and 26
framed it as a "budgeting allowance" or "placeholder" rather than an expected loss.
Half (15/30) said outright that the policy does not contain enough information to
calculate a dollar risk. The typical answer therefore did two things at once: it
supplied the specific yearly figure the user asked for, and told the user not to
rely on it.

**Figures came from a short menu of round numbers.** 27 of the 30 figures were
exactly $10, $25, $50 or $100; $25 alone accounted for 12. The pooled median was
$25 and the range $0–$100. Where the model showed its working, the itemized
scenarios were constructed to sum to the round headline figure: one X response
assumed a 1% chance of a $1,000 loss, 5% of $200 and 10% of $50, totalling exactly
$25; another assumed 1% of $2,000, 2% of $500 and 10% of $200, totalling exactly
$50. The probabilities and loss sizes were labelled as assumptions, not drawn from
the policy. This pattern is more consistent with the model choosing a plausible
figure and then illustrating it than with deriving a figure from the policy's
content.

**Stability.** Repeating the identical prompt on the identical policy produced
figures that varied by up to a factor of ten (ChatGPT: $10 to $100; X: $15 to
$100). Four of the six services had a CV above 0.5 (0.53–0.84), the threshold we
set for treating a dollar estimate as not reproducible. Google was the exception:
$100 in all five runs (CV 0). That is perfectly consistent, but since $100 was also
the largest figure the model gave any service, it may reflect a ceiling on the
menu rather than a policy-specific judgment. Mean figures did not trend across the
five rounds (round means $38, $58, $50, $53, $37), and the interface showed the same
model name throughout.

**Ordering.** By mean, P1 ranks Google > X > ChatGPT > LinkedIn > Netflix > PayPal.
This ordering is fragile: four of the six services share a median of $25, so their
relative positions rest on one or two runs each (ChatGPT's mean, for example, is
lifted by a single $100). PayPal, the service with the most direct access to
financial data in our set, received the *lowest* mean. Its five figures include the
one borderline response in the dataset (below).

**What P1 priced.** Because P1 does not say what kind of harm to price, the model
priced a broad mix: costs from targeted advertising and influenced spending
(mentioned in 25/30 responses), identity theft or breach exposure (24/30), time
spent dealing with privacy problems, and the effects of automated profiling. A P1
figure is therefore not the same quantity as our identity-theft-based calculation,
which is one reason P2 specifies the harm. 13 of 30 responses cited an external
statistic (FTC, Federal Reserve or Bureau of Justice Statistics fraud figures), in
each case noting that it could not be attributed to the specific service.

**One borderline response.** One PayPal response stated that "the direct annual cost
is $0" and called the remaining risk unquantifiable, alongside an explicitly
hypothetical $20 calculation. Under our pre-set coding rules this is a single stated
figure and was recorded as $0. Treating it as a refusal instead would raise PayPal's
P1 mean from $25 to $31 and lower its CV from 0.71 to 0.40, without changing its
position as the lowest-ranked service.

### P2: the profiled question

**Table [N+1].** [Same layout as Table N, for P2.]

**Stability.** [CV range under P2; how many of six exceed 0.5; whether the fixed
format reduced variability relative to P1.]

**Refusals.** [P1 had none (0/30). P2: rate, and what refusals looked like.]

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
- **Different inputs.** Our calculation is driven by each company's breach
  history; the model saw only the policy text. Disagreement in ordering may mean
  the two are measuring different things (what a service *collects* vs how often
  it has *lost* data), not that either is wrong. Zero-breach services (ChatGPT,
  Netflix) score $0 in our calculation by construction, which no policy-reading
  model would reproduce.
- **Hedged compliance (from P1).** Asked naively, the model neither refused nor
  committed: it produced the requested figure while stating, in nearly every
  response, that the figure was not a real estimate. A user reading only the
  headline number would come away with a precise-looking figure the model itself
  says is unfounded; a user reading the caveats would come away with no number at
  all. Either way, P1 does not deliver a usable risk estimate.
- **Refusals as a design feature.** A model that declines to give a number may be
  behaving more responsibly than one that produces a confident figure.

---

## Limitations

*Specific to this portion. Keep both kinds the course asks for: constraints of a
class project, and limits that would remain with more resources.*

- **No ground truth.** No published source gives the true annual dollar risk of
  accepting a privacy policy. We can measure the model's consistency and its
  agreement with our calculation, but neither establishes that either is correct.
- **Prompts run on separate days.** P1 and P2 were collected on consecutive days
  rather than interleaved, so a model change between days would be confounded with
  the prompt effect.
- **One model, one interface.** Results describe [model] as served through its web
  interface during [dates], not LLMs in general. The provider may update the model
  without notice; rounds spread this across services but cannot remove it.
- **Uncontrolled sampling.** Temperature, system prompt and seed are not exposed by
  the web interface, so variability cannot be split into sampling and prompt
  effects.
- **Long inputs.** Policies of 29k–77k characters are long for a single message;
  models are known to weigh content unevenly across long inputs, so clauses deep in
  a policy may influence the estimate less than early ones.
- **Ties in the comparison.** Two of six services score exactly $0 in our
  calculation (no qualifying breaches), so the team ranking has a tie at the bottom,
  further reducing what a rank correlation over six services can show.
- **Small n.** Five repeats per cell gives a usable but imprecise standard
  deviation, and six services gives little power for a rank correlation.
- **Manual coding.** Figures were read from free-text answers by one coder applying
  fixed rules. An audit of all P1 rows against the saved responses found and
  corrected three transcription slips (runs 8, 14, 15); each correction is noted in
  the run log, and every logged figure can be checked against the full response.
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
