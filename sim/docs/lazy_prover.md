# Lazy-prover gap: comparison of fixes (v0.2.1)

**All numbers are simulation outputs under illustrative parameters** (Params defaults in `sim/v02/core.py`, 30 seeds, mean ± 95% CI from a t-interval).
Run with `python3 sim/v02/exp_lazy.py 30`. Raw output is in `sim/v02/results_lazy.json` and `.log`.
`core_v02_frozen.py` keeps the exact v0.2 code. The new options default to v0.2 behaviour, and a spot check gives identical recall (seed 3: 0.6047 in both).

## Problem
Lazy provers (ptype 1) never search. They are paid only through BSAFE claims that go unrefuted, and in the v0.2 baseline they earn 15.7 ± 0.6 against 83.3 ± 0.9 for honest provers, a ratio of 0.189 ± 0.008.
v0.2 has no effort cost at all, so 0.19 is an upper bound on how well honest work is rewarded relative to laziness. Once search has a cost, the gap gets worse.

## Fixes modelled
New parameters:
- `safe_pay_rule`:
  - `base`: v0.2 behaviour, BSAFE pays β_safe(1−q)^θ.
  - `tied`: BSAFE pay is zeroed when the contract carried a planted mutant and the poster did not kill it.
  - `kill_required`: BSAFE pays only if the poster killed a mutant on that contract.
- `mutant_rate` ∈ {0.3 (v0.2), 0.6, 0.9}: the "denser mutants" option.
- `search_cost` c ∈ {0, 0.1} per routed task searched, charged to searchers only.

## Results: lazy/honest pay ratio (lower is better; < 0 means laziness loses money)
| c | rule | mr=0.3 | mr=0.6 | mr=0.9 |
|---|---|---|---|---|
| 0 | base | 0.189±0.008 | 0.143±0.007 | 0.111±0.006 |
| 0 | tied | 0.122±0.008 | 0.037±0.005 | −0.015±0.004 |
| 0 | kill_required | −0.054±0.006 | −0.038±0.004 | −0.030±0.004 |
| 0.1 | base | 0.408±0.020 | 0.239±0.012 | 0.164±0.009 |
| 0.1 | tied | 0.268±0.018 | 0.063±0.009 | −0.022±0.006 |
| 0.1 | kill_required | −0.157±0.018 | −0.068±0.008 | −0.045±0.004 |

Absolute pay (c = 0):

| Rule | Lazy pay (mr 0.3 / 0.6 / 0.9) | Honest pay (mr 0.3 / 0.6 / 0.9) |
|---|---|---|
| base | 15.7 / 15.7 / 15.4 | 83.3 / 110.0 / 138.2 |
| tied | 10.0 / 4.0 / −2.0 | 82.1 / 107.6 / 134.6 |
| kill_required | −3.7 / −3.8 / −4.0 | 68.5 / 100.2 / 132.6 |

Recall (≈0.59) and false-safe survival (0.12–0.14, CIs overlap) do not change under any rule. The fixes move money; they do not change detection in this model.

## Reading
1. **Denser mutants alone do not touch lazy income.** Lazy pay stays flat at about 15.5. The ratio falls only because honest provers collect more mutant rewards J. That is a pure transfer from the mutant budget (J × mutants), and it gets weaker once search has a cost: at c = 0.1 and mr = 0.9 the ratio is still 0.164.
2. **Tying safe-claim pay to kills** works roughly in proportion to mutant density. Lazy pay on BSAFE falls by about the factor (1 − mr), so it needs mr ≳ 0.6 to bite. At mr = 0.9 lazy income turns negative. Honest provers lose very little (≤ 3%), because they only miss the 1 − d = 20% of mutants they fail to detect.
3. **No pay without a kill** removes lazy BSAFE income entirely at any density. The remaining loss of about −4 comes from refutation slashes. The price is that honest provers lose all BSAFE pay on mutant-free contracts: −18% at mr = 0.3, −2% at mr = 0.9. It also means BSAFE gets paid only on contracts with a mutant, which pushes toward planting a mutant in almost every contract.
4. **Recommended combination (still illustrative):** `tied` with mr ≈ 0.6–0.9 matches `kill_required` on the lazy ratio while keeping honest BSAFE income. With dense mutants the two rules converge (at mr = 0.9: −0.015 vs −0.030).
5. **Caveat that dominates everything above:** all three fixes assume a prover cannot tell planted mutants from real tasks. If it can, a lazy prover searches only the tasks that look like mutants and none of these numbers hold. See `spotcheck_auc.md`.

## Not modelled
- The cost of generating and verifying mutants (only J is paid out).
- Mutant density changing how much FV budget each task gets.
- Lazy provers adapting by partially searching.
