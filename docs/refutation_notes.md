# Causal Audit: Refutation Test Results (Mid Review)

**Author:** Member 2 (Sharath) | **Script:** `backend/refutation.py` | **Raw output:** `docs/refutation_output.txt`
**Data:** `data/customers_causal.csv` (synthetic, 5,000 customers, so the true effects are known)

## What a refutation test is
A refutation test tries to *break* a causal estimate. Passing does not **prove** causality. It shows the estimate is not an artefact of the pipeline and that it reacts the way a real causal effect should. Careful wording for the viva: the estimate **survived** the tests, or the tests **failed to refute** it.

## Part A: DoWhy refuters ($10 discount vs no discount, linear backdoor estimator)
Estimated effect: **+0.0414** (true effect for discounted customers: +0.0345).

| Test | What should happen | Result |
|---|---|---|
| Placebo treatment (shuffled discount) | Effect falls to about 0 | **+0.0018** (p = 0.88). Pass |
| Random common cause (add a noise confounder) | Effect unchanged | **+0.0414** (p = 0.90). Pass |
| Data subset (random 80%) | Effect stable | **+0.0397** (p = 0.86). Pass |
| Unobserved common cause, strength 0.02 | Effect shrinks gradually | +0.0433 |
| Unobserved common cause, strength 0.1 | Effect shrinks gradually | **+0.0157** (about 60% smaller) |
| Unobserved common cause, strength 0.5 | Effect shrinks gradually | **-0.0293** (sign flips) |

## Part B: our from-scratch Double ML
Mean ITE of a $10 discount: **+0.0283** (true mean +0.0371; correlation with truth 0.908).

| Test | Result |
|---|---|
| Placebo (shuffled discount, 15 runs) | Mean -0.0011 (sd 0.0070). The real estimate is 4.1 placebo SDs from 0, and 0 of 15 placebo runs were as large. Pass |
| Random common cause (+ noise column, 15 runs) | +0.0272, shift -0.0012. Pass |
| Data subset (80%, 15 runs) | +0.0275, shift -0.0008. Pass |

## Sensitivity check: forgetting a real confounder
This experiment *should* make the estimate worse.

| Features used | Mean ITE | Correlation with truth | RMSE vs truth |
|---|---|---|---|
| all four | +0.0283 | 0.908 | 0.0309 |
| without `previous_purchases` | **-0.0229** | 0.937 | 0.0650 |
| without `engagement` | +0.0396 | 0.826 | 0.0340 |

## What we can and cannot claim
**We can say:**
- The estimate is stable across resampling, added noise and subsetting (no sign of a pipeline artefact).
- A shuffled discount produces no effect, so the estimate is tied to the real treatment.
- Adjusting for confounders matters: leaving out `previous_purchases` flips the mean effect from positive to negative and doubles the error.

**We cannot say:**
- That no hidden confounder exists. The random-common-cause test adds *irrelevant* noise, so it cannot detect a *relevant* missing variable. On real data, "no unobserved confounding" is an untestable assumption. In our synthetic data we know all confounders are observed because we built it that way.
- That the effect is robust to strong hidden confounding. The sensitivity test shows a hidden cause of strength 0.1 would cut the effect by about 60%, and strength 0.5 would flip its sign. (DoWhy's strength scale is relative to the data, so read this as "fairly fragile", not as an exact threshold.)

**Ranking is more robust than the level.** Dropping `previous_purchases` ruins the average (+0.028 to -0.023) but the ranking correlation stays high (0.937, even slightly up). Dropping `engagement` does the opposite: the mean barely moves but the correlation falls to 0.826. This is consistent with `engagement` driving the *differences* in effect between customers in our data, whereas `previous_purchases` mainly drives who got a discount. The optimizer in Week 3 relies on ranking, which is the safer part, but any dollar-value claim should be hedged.

## Viva answers in one line each
- **Placebo test?** Replace the real treatment with a random one. A genuine causal estimate should drop to about zero.
- **Random common cause?** Add an irrelevant variable. A well-adjusted estimate should not change.
- **Data subset?** Re-estimate on subsets. A stable estimate is not driven by a few customers.
- **Unobserved common cause?** Simulate a hidden confounder of growing strength to see how fragile the conclusion is.
- **What if a test fails?** The estimate is probably driven by something other than the treatment (a pipeline problem or an omitted confounder), so we would revisit the DAG and the adjustment set.

## Limitations
- Part A uses DoWhy's linear estimator, so it audits a simple model. Part B repeats the attacks on our Double ML.
- The tests use synthetic data. Real campaigns need domain knowledge to defend the "no hidden confounders" assumption.
- 15 repetitions limit the resolution of the Part B placebo p-value (the smallest possible is about 0.07).
