# rho_bnd fit from Halmos runs (v0.2.2)

**The sample is very small: 46 runs, 8 targets, of which 5 are buggy, all toy or synthetic. Runs at different k on the same target are not independent. Read every CI below as "consistent with almost anything in the interval".**
Data and method notes come from Verification Researcher: `/workspace/research/two-tier-market/data/rho_bnd_runs.csv` and `rho_bnd_notes.md`.
Code: `sim/rho/fit_rho.py` produces `rho_fit.json`, and `sim/v02/exp_rho_fit.py` produces `results_rho_fit.json`.
CIs are 95% Wilson intervals over targets. Market numbers are simulation outputs under illustrative parameters.

## Two quantities that must not be confused
- **Miss rate** m(k) = P(bounded check at k returns "safe" | contract buggy). The data notes call this rho_bnd.
- **Sim weight** ρ_bnd = P(contract truly safe | bounded "safe" claim survives). This is the partial-settlement weight in `core.py` and the parameter that sets the inflation tilt q/(q+(1−q)ρ).
- They are linked by Bayes, with prior bug rate π among claimed contracts and specificity s:
  ρ = (1−π)s / ((1−π)s + π·m(k)).
- The data has no false cex (0/16 completed runs on fixed targets), so I use s = 1.

## Timeout treatment (stated choice)
- A timeout or error produces no cex, so the bug goes unreported. **For the miss rate, a timeout counts as a miss** (the operational view). I also report the alternative that excludes timeouts.
- A timeout is not a "safe" verdict, so it cannot back a BSAFE claim. **For ρ, timeouts are excluded from the claims** (they lead to escalation or no claim).
- Every run at k = 8 timed out, so k = 8 has no safe verdicts. Its miss rate under the timeout-as-miss rule is 4/4.

## Miss rate m(k), 5 buggy targets
| k | safe / cex / timeout | m(k), timeout = miss [95% CI] | m(k), timeout excluded |
|---|---|---|---|
| 1 | 5/0/0 | 1.00 [0.57, 1] | 1.00 [0.57, 1] |
| 2 | 4/1/0 | 0.80 [0.38, 0.96] | same |
| 3 | 2/3/0 | 0.40 [0.12, 0.77] | same |
| 4 | 1/3/1 | 0.40 [0.12, 0.77] | 0.25 [0.05, 0.70] |
| 6 | 1/3/0 | 0.25 [0.05, 0.70] (n = 4; GateM6 was skipped after its k4 timeout) | same |
| 8 | 0/0/4 | 1.00 [0.51, 1] | n/a |

**Depth model:** a step model, "cex iff k ≥ bug depth and the run completes", explains **23/23** completed buggy runs. A smooth parametric fit, such as logistic in k − depth, is not justified because the data are perfectly separated. So:
  m(k) = P(D > k) + P(D ≤ k, run at k does not finish).
- The completion horizon in this harness is k ≲ 6 at 30–60 s solver timeouts (k8 always timed out; GateM6 timed out at k4).
- **The bug-depth distribution P(D > k) for real contracts is unmeasured, and it is the quantity that actually matters.** Over these 5 targets the depths are {2, 3, 3, 6, 10}, but they were chosen by construction, so they are not a sample of real bugs.

## Sim weight ρ_bnd(k) = P(truly safe | safe verdict), using the upper/lower m CI
| k | sample composition π = 5/8 (raw safe-verdict ratio, Wilson) | π = 0.3 | π = 0.1 (sim base_rate) |
|---|---|---|---|
| 1 | 0.375 [0.14, 0.69] | 0.70 [0.70, 0.81] | 0.90 [0.90, 0.94] |
| 2 | 0.43 [0.16, 0.75] | 0.75 [0.71, 0.86] | 0.92 [0.90, 0.96] |
| 3 | 0.60 [0.23, 0.88] | 0.85 [0.75, 0.95] | 0.96 [0.92, 0.99] |
| 4 | 0.75 [0.30, 0.95] | 0.85 [0.75, 0.95] | 0.96 [0.92, 0.99] |
| 6 | 0.67 [0.21, 0.94] | 0.90 [0.77, 0.98] | 0.97 [0.93, 0.995] |

The π = 0.3 and π = 0.1 columns plug the timeout-as-miss m(k) CI into Bayes. The π = 5/8 column is the direct ratio, fixed-safe / all-safe. The v0.2 anchor (5/7 = 0.71) sits inside these ranges.

## Does the inflation tilt bite? (E2 rerun at the fitted values)
Setup: 20% inflators and 20% lazy screeners, η = 0.3, 30 seeds. The value shown is inflator pay minus honest pay, ± 95% CI.

| ρ_bnd | 0.375 | 0.438 | 0.5 | 0.6 | 0.706 | 0.90 | 0.921 | 0.957 | 0.973 |
|---|---|---|---|---|---|---|---|---|---|
| infl − honest | +1.91±0.32 | +1.29±0.34 | +0.68±0.35 | −0.30±0.38 | −1.34±0.41 | −3.24±0.47 | −3.44±0.47 | −3.80±0.49 | −3.95±0.49 |

The crossover is between ρ = 0.5 and 0.6. ρ = 0.6 is not significantly different from 0.

**Verdict:**
- **At the sim's base rate (π = 0.1), the tilt does not bite at any k.** The lower CI for ρ is ≥ 0.90 at every k from 1 to 6, so inflators lose to honest screeners by about 3–4.
- **It does bite when claimed contracts are bug-heavy with shallow bounds:** π ≳ 0.6 at k ≤ 2, or the lower CIs at k ≤ 6.
- **The robust route** is to make ρ depth- and k-dependent, ρ(k, depth class), or to use the defenses in `analysis.md` (report-independent reference, deferral of the 1−ρ remainder), rather than relying on ρ being high.
- **This rests on two unmeasured inputs.** The first is the true bug prior among contracts that receive BSAFE claims (π). The second is the depth distribution of real bugs relative to the completion horizon k ≈ 6. Bugs deeper than about 6 transactions are always missed (m = 1), so if they are common among the bugs that are present, ρ falls toward 1−π and the tilt returns.

## Next measurement
The next step is to run the dataset mutants (2,093, once a generic harness exists) to estimate P(D > k). That turns this into a usable ρ(k).

## Update (v0.3)
The sim can now derive ρ from k and the depth distribution (`docs/rho_depth.md`). A Bayes-consistent ρ is always ≥ 1−π, and across 216 configurations inflators never beat honest screeners significantly.
