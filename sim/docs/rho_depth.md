# v0.3: rho_bnd as a function of bound k and bug depth

**Numbers are simulation outputs under illustrative parameters.** The depth distributions are parametric placeholders until Verification Researcher's 2,093-mutant per-mutant depth CSV arrives. The empirical anchor is still 5 buggy toy targets (`rho_bnd_fit.md`).

## Model (`v02/depth.py`)
- **Per-task bug depth** D ≥ 1 comes from a pluggable distribution:
  - `Geometric(g)` (default g = 0.5): P(D>k) = g^k.
  - `DiscretePareto(α)`: P(D>k) = k^−α, a polynomial tail.
  - `Empirical(...)`, built with `load_depth_csv(path)`.
- **Detection (fitted rule):** a counterexample appears iff k ≥ D and the run completes, with the existing searcher factor `detect` on top. Use `detect=1` for the pure rule.
  - Timeouts: `p_complete(k)` defaults to no timeouts; `step_timeout(k_max)` makes runs complete iff k ≤ k_max (the fitted value is about 6).
  - Depth and completion draws use a separate RNG stream (`[seed, epoch, 7]`).
- **ρ by Bayes:**
  - miss(k) = 1 − detect·(1 − P(D>k))·p_complete(k)
  - ρ(k) = (1−π) / ((1−π) + π·miss(k)), where π = `base_rate` and specificity is 1 (no false cex observed).
  - Every no-cex task resolves as bounded-safe in the sim, so a timeout counts as no cex.
- **Modes:** `Params.rho_mode="flat"` (the default) uses `rho_bnd` and is bit-identical to v0.2: `results_v02.json` regenerates with no diff, and in flat mode the depth parameters are never read. `rho_mode="depth"` uses `bound_k`, `depth_dist` and `p_complete`. The ρ actually used is returned as `out["rho_safe"]`.

## Empirical CSV schema (for the 2,093-mutant rerun)
Header names are case-insensitive, and the first matching column wins.

| role | accepted names | values |
|---|---|---|
| depth (required) | `depth`, `bug_depth`, `bug_min_depth`, `min_depth`, `min_k`, `first_cex_k`, `cex_k` | integer ≥ 1 = smallest k with a replayed cex. Blank, `inf`, `none`, `na`, `nan` or `>K` (not found up to K) are read as D = ∞, which is conservative. |
| buggy filter (optional) | `ground_truth_buggy`, `buggy`, `is_buggy` | keep rows with 1/true/yes |
| weight (optional) | `weight`, `count`, `n` | row weight |

Note: a censored `>K` is read as never found. Once a real tail exists, refit with an explicit censoring model.

## Sweep (`v02/exp_depth.py` → `results_depth.json` / `.log`)
- **Grid:** π ∈ {0.1, 0.3, 0.5} × 6 depth distributions (geometric g = 0.3, 0.5, 0.7, 0.85; Pareto α = 1, 0.5) × timeouts {none, step at 6} × k ∈ {1, 2, 3, 4, 6, 8}.
- **Runs:** 216 configurations, 30 seeds each, on the E2 world (20% inflators, 20% lazy screeners, η = 0.3), with `detect=1`.
- **Metric:** inflator pay minus honest pay, mean ± 95% CI.

Excerpt at π = 0.5, no timeouts, shown as ρ / (inflator − honest):

| dist | k=1 | k=2 | k=4 | k=8 |
|---|---|---|---|---|
| geom 0.3 | 0.77 / −2.68±0.71 | 0.92 / −4.00±0.74 | 0.99 / −4.61±0.95 | 1.00 / −4.90±0.88 |
| geom 0.85 | 0.54 / −1.23±0.83 | 0.58 / −1.14±0.63 | 0.66 / −1.88±0.73 | 0.79 / −3.07±0.50 |
| Pareto 0.5 | 0.50 / −0.56±0.61 | 0.59 / −1.70±0.63 | 0.67 / −1.91±0.77 | 0.74 / −2.05±0.66 |

With the step timeout at 6, every k = 8 cell collapses to ρ = 1−π (−0.56 ± 0.61 at π = 0.5; −3.80 ± 0.49 at π = 0.3).

## Findings
1. **In 0 of 216 configurations do inflators beat honest screeners significantly.** A Bayes-consistent ρ is bounded below by 1−π, since miss ≤ 1. The v0.2 E2 result that inflators profit at ρ ≤ 0.5 needed a flat ρ far below 1−π = 0.9, i.e. a weight the depth model cannot produce at π = 0.1.
2. **The tilt gets closest to biting when ρ approaches 1−π.** That happens with a heavy depth tail and shallow k (Pareto α = 0.5 at k = 1), or with k beyond the completion horizon, where every run times out. At π = 0.5 the gap is −0.56 ± 0.61, not distinguishable from 0. Extrapolating that trend (not run), claimed-contract bug rates above about 0.5 with deep or unreachable bugs are where it would bite.
3. **A larger k helps only up to the timeout horizon.** Past it (k = 8 with the step at 6), ρ falls back to 1−π and recall drops. The best k is the largest one that completes, which matches `rho_bnd_fit.md`.
4. **Heavier depth tails lower ρ at every k.** At π = 0.3 and k = 4, ρ is 1.00 for g = 0.3 and 0.82 for g = 0.85 or Pareto 0.5. The incentive damage stays small here, but recall suffers. The real risk from deep bugs is undetected bugs, not inflator profit.
5. **Remaining exposure:** the protection relies on ρ actually being derived from a well-estimated π and depth distribution. A mis-specified ρ, set too low, reintroduces the v0.2 tilt. Estimating P(D>k) from the mutant rerun is the next step.
