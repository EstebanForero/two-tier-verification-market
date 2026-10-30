# Spot-check detectability vs. probe AUC (v0.2.1)

Motivation: `/workspace/ideation/novelty-watch-1.md` (internal note), suggestion 2. Mutants can be fingerprinted, so the spot-check IC condition has to hold against an agent that runs a probe with AUC α.
**All numbers are simulation outputs or closed-form evaluations under illustrative parameters.** The code is `sim/v02/spotcheck.py` (`python3 spotcheck.py 30`), with output in `results_spotcheck.json` and `.log`.

## Model
- Each task is either a planted spot check (a mutant) with probability s, or a real task.
- The agent chooses either full effort, at cost c, or shirking.
- On a **real** task, shirking saves G = c − ΔR > 0, where ΔR is the expected real reward lost by not searching.
- On a **spot check**, full effort kills the mutant with probability d and earns J. An unkilled spot check is penalised P.
  - Expected payoff with full effort: dJ − (1−d)P − c.
  - Expected payoff when shirking: −P.
  - So shirking on a spot check loses **D = d(J+P) − c**.
- The agent observes a detector signal before choosing.

Indifference on a task with posterior spot-check probability π: full effort is weakly preferred iff π·D ≥ (1−π)·G. Written as a likelihood ratio:

  full effort on signal x  ⇔  LR(x) := P(x|real)/P(x|spot) ≤ K,  where  **K = s·D / ((1−s)·G)**.

The binding case is shirk-on-unflagged: the agent works wherever the probe says "mutant" and shirks wherever it says "real". IC therefore has to hold on the most real-looking signals.

## (A) Binary flag, TPR t, FPR f
- On a flagged task, LR = f/t < 1, so working there is easy to sustain.
- On an unflagged task, LR = Λ = (1−f)/(1−t), which is the binding constraint.
- Full effort is a best response iff D ≥ G·Λ·(1−s)/s, which gives:

  **P*(s) = [c + G·Λ·(1−s)/s]/d − J,  s*(P) = G·Λ / (G·Λ + d(J+P) − c).**

For a single operating point, AUC = (1 + t − f)/2. At fixed AUC, Λ(f) = (1−f)/(2−2α−f) increases with f. Its minimum is at f = 0, **Λ_min(α) = 1/(2(1−α))**, and it is unbounded as t → 1. *(Correction: an earlier draft called 1/(2(1−α)) the worst case. It is the designer's best case.)* Substituting Λ_min into P* and s* therefore gives a **lower bound** on the required penalty and rate. At α = 0.5, Λ = 1 and the result is the classic TrueBit-style condition s·D ≥ (1−s)·G.

## (B) Continuous score (binormal, the realistic case)
- Scores: spot ~ N(δ,1), real ~ N(0,1), with α = Φ(δ/√2), so δ = √2·Φ⁻¹(α).
- LR(z) = exp(−δz + δ²/2) is unbounded as z → −∞.
- **So exact full-effort IC cannot be reached with a bounded penalty for any α > 0.5.** The agent shirks on the tasks that look most real.

The best response is to shirk iff z < z* = δ/2 − ln K/δ. The shirk fraction on real tasks is Φ(z*), and on spot checks it is Φ(z* − δ), which is how often a shirk gets caught.

**ε-IC** (shirk on at most a fraction ε of real tasks) holds iff ln K ≥ δ²/2 − δ·Φ⁻¹(ε). This gives:

  **P_ε(α,s) = [c + G·(1−s)/s · exp(δ²/2 − δ Φ⁻¹(ε))]/d − J**
  **s_ε(α,P) = G·M / (G·M + d(J+P) − c),  M = exp(δ²/2 − δΦ⁻¹(ε))**

The required penalty grows like exp(δ²/2 + δ|z_ε|), which is super-exponential in Φ⁻¹(α). Penalties are capped by the bond or stake, so there is a maximum probe AUC beyond which spot checks cannot enforce effort.

## Sweep (c=0.1, G=0.05, d=0.8, J=1, s=0.1, ε=0.05; illustrative)
- **P_ε** is the penalty needed for 5% shirking under the binormal model.
- **P_bin** is the penalty under the binary flag with Λ_min, so it is a lower bound.
- **s_ε @P=5** is the spot-check rate needed when the penalty is 5.
- **Naive design** uses P = 0, which is IC at α = 0.5 with K = 1.56.
- The **MC** columns come from an agent that learns the best shirk threshold on one 20k-task sample and is scored on a fresh one. 30 seeds, mean ± 95% CI.

| α | P_ε | P_bin (lower bound) | s_ε @P=5 | naive shirk (closed) | naive shirk (MC) | naive gain/task (MC) | ε-design shirk (MC) |
|---|---|---|---|---|---|---|---|
| 0.50 | 0 | 0 | 0.011 | 0.000 | 0.003±0.001 | −0.0001±0.0001 | 0.003±0.001 |
| 0.55 | 0 | 0 | 0.014 | 0.008 | 0.030±0.013 | −0.0002±0.0002 | 0.030±0.013 |
| 0.60 | 0.21 | 0 | 0.020 | 0.146 | 0.146±0.022 | 0.0008±0.0002 | 0.063±0.016 |
| 0.70 | 1.63 | 0.06 | 0.045 | 0.411 | 0.411±0.023 | 0.0064±0.0003 | 0.060±0.011 |
| 0.80 | 7.22 | 0.53 | 0.133 | 0.589 | 0.593±0.015 | 0.0146±0.0003 | 0.063±0.013 |
| 0.90 | 56.4 | 1.94 | 0.520 | 0.746 | 0.746±0.012 | 0.0246±0.0002 | 0.074±0.014 |
| 0.95 | 385 | 4.75 | 0.880 | 0.835 | 0.835±0.008 | 0.0313±0.0002 | 0.156±0.021 |

## Findings
1. **The closed form matches the MC.** Naive-design shirk fractions agree to within the CIs from α = 0.6 up. At α ≤ 0.55 the MC shirks a little on noise, but the gain is ≤ 0.
2. **AUC-blind spot checks fail quickly.** A design that is IC with 56% slack against a blind agent sees 41% shirking on real tasks at α = 0.7, and 75% at α = 0.9.
3. **The penalty or rate cost explodes with AUC.** For 5% shirking, the needed penalty goes 0.2 → 1.6 → 7.2 → 56 → 385 as α goes 0.6 → 0.95, i.e. more than 1000× the bounty scale. At a fixed P = 5, the needed spot-check rate goes from about 1% to 88%, at which point the "spot checks" are most of the work.
4. **Binary-flag results understate the problem.** Even the most favourable binary detector (f = 0) gives P_bin far below P_ε, and a binary flag with TPR → 1 makes IC impossible. Any analysis that assumes a fixed TPR/FPR flag at a given AUC is optimistic unless it uses the actual operating point. The bound has to use the full ROC, specifically its likelihood-ratio tail.
5. **MC ε-design shirking runs slightly above ε (0.06–0.07, and 0.16 at α = 0.95).** Near indifference the learner's objective is flat, so finite-sample threshold noise pushes it a little past z*. Its gain is ≈ 0 (≤ 0.0004 ± 0.0016 per task), so this does not show the closed form is wrong.
6. **Design implication.** Mutant indistinguishability has to be engineered and measured, not assumed:
   - Release spot checks only with a red-team probe AUC ≤ about 0.6 (illustrative).
   - Bound the realistic bond as P ≤ stake, and solve P_ε(α) ≤ stake for the maximum tolerable α.
   - Prefer spot checks that are real historical bugs or real contracts over synthetic mutants, which are the fingerprintable ones per the novelty-watch note.
   - This combines with `lazy_prover.md`: the `tied` / `kill_required` fixes rely on the same indistinguishability.

## Limitations
- Equal-variance binormal ROC only. A different ROC tail changes M; the general rule is M = sup over the shirk region of LR.
- Risk-neutral agent, with G and d held constant across tasks.
- No repeated-game reputation effects.
- The agent knows s.
