# Week 2 Report: Propensity Score Matching and Balance Checks

**Author:** Member 2 (Sharath) | **Code:** `backend/propensity.py` | **Figures:** `backend/figures/`
**Data:** `data/customers_causal.csv`. We compare the **$10 discount** (1,278 customers) with **no discount** (2,598 customers); customers who got $20 are left out so the treatment is yes/no.

## Goal
The brief asks us to "balance historical observational data, simulating a randomized A/B test without actually running one." Discounts were not random, so discounted and non-discounted customers differ. We match each discounted customer to a lookalike who did not get one, so the two groups can be compared fairly.

## Method
1. **Propensity score** `e(X)` = the probability of getting a discount given the covariates, from a logistic regression on polynomial features.
2. **Overlap check:** scores for both groups run from about 0.09 to 0.65, so every discounted customer has comparable non-discounted customers.
3. **Matching:** each discounted customer is matched 1:1, with replacement, to the nearest control on the logit of the score, inside a caliper of 0.2 standard deviations (Austin, 2011). All 1,278 treated customers were matched, using 858 distinct controls.
4. **Balance:** standardized mean difference (SMD) of each covariate before and after. A common rule of thumb is that |SMD| below 0.1 means balanced.
5. **Effect:** the average effect on the treated (ATT), with IPW (inverse propensity weighting) as a cross-check.

## Balance results
| Covariate | SMD before | SMD after | Balanced? |
|---|---|---|---|
| `previous_purchases` | -0.398 | 0.012 | yes |
| `engagement` | +0.335 | 0.019 | yes |
| `price_sensitivity` | +0.012 | 0.021 | yes |
| `age` | -0.002 | 0.010 | yes |

Before matching, discounted customers had far fewer previous purchases and higher engagement. After matching, all four covariates are well within the 0.1 threshold. This is the main result of the matching step. See `propensity_overlap.png` and `balance_love_plot.png`.

## Effect estimates (effect of a $10 discount, for discounted customers)
| Method | Estimate |
|---|---|
| Naive difference | +0.013 |
| Matched ATT | +0.016 |
| IPW ATT (cross-check) | +0.037 |
| **True ATT** | **+0.035** |

Full-pipeline bootstrap (200 resamples, refitting the propensity model each time):

| Method | Standard error | 95% interval | Contains true ATT? |
|---|---|---|---|
| Matched ATT | 0.027 | [-0.007, +0.100] | yes |
| IPW ATT | 0.017 | [+0.003, +0.071] | yes |

## What this does and does not show
- **Matching fixes the imbalance.** All covariates are balanced afterwards.
- **The effect estimates are noisy.** With about 3,900 customers and a small true effect (3.5 percentage points), the matched estimate (+0.016) cannot be told apart from the truth (+0.035). Its interval is wide. IPW uses all the controls and is more precise (SE 0.017 vs 0.027).
- **Do not quote one number as "the" effect.** The two estimators differ by more than 2x here, and that difference is within their noise.
- **Bootstrap caveat:** the standard bootstrap is known to be unreliable for nearest-neighbour matching with replacement, so read the matched interval as a rough guide only.
- **Balance is not proof of causality.** It only shows we balanced the *observed* covariates. Hidden confounders would not be fixed (see `refutation_notes.md`).

## How this fits with Double ML
Matching and IPW use the propensity score to compare groups. Double ML uses a model of the treatment (the same `E[T|X]` idea) inside its estimator, and lets the effect vary per customer. Matching gives us a transparent balance check and a second opinion on the average effect, and Double ML gives us individual effects for the optimizer.
