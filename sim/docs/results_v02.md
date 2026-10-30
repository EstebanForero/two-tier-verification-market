# Results v0.2: simulation outputs under illustrative parameters

**Every number here is a simulation output under illustrative parameters (`sim/v02/core.py::Params`). None is an empirical claim.**

- **Runs:** 30 seeds per cell. Values are mean ± 95% CI half-width (t-distribution, df = 29).
- **Each run:** 1,000 tasks × 10 epochs, 20 ML screeners, 10 provers.
- **Raw outputs:** `sim/v02/results_v02.json`.
- **Reproduce:** `python sim/v02/experiments.py 30` (about 1 minute).

## Data anchors from the repo
The only empirical mutant/vulnerability data in `/workspace/research/two-tier-market` is `verification/pipeline/results_halmos.json` (plus `halmos_run.log`). It contains 17 Halmos checks over 7 toy target families (F = fixed, M = mutant, V = vulnerable).
- **Killed:** 6/7 V variants and 2/3 M variants, so 8/10 buggy variants were killed. Both survivors are in the Xfer family (`XferV`, `XferM_delreq`).
- **Passed:** 7 checks, of which 5 were truly safe, so P(safe | pass) = 5/7 ≈ 0.71. `MulF` exited with code 2 (error) and is excluded.
- **Parameters set from this:** `detect = 0.8` and the default `rho_bnd = 0.71`.
- **Caveat:** n is tiny and the targets are toys. These are anchors, not estimates. ρ_bnd is swept in E2 while we wait for Verification Researcher data.

## Attack mix (E1)
- **Screeners:** 40% deflators (target-task reports × 0.3), 20% lazy (report the base rate), 40% honest.
- **Targets:** 10% of tasks. Base rate 0.1. FV budget 15% of tasks.
- **ML scoring:** only on the uniform-exploration (audit) set, against a leave-one-out reference (same aggregator without the scored screener).

### E1: Aggregator × η, recall on target bugs (main question)
| aggregator | η=0 | η=0.1 | η=0.3 |
|---|---|---|---|
| median (unweighted) | 0.218 ± 0.017 | 0.211 ± 0.011 | 0.193 ± 0.011 |
| **stake-capped trimmed** log-odds (cap = 1, trim 25%/tail) | **0.313 ± 0.020** | **0.307 ± 0.013** | **0.273 ± 0.014** |
| uncapped stake-weighted log-odds mean, equal stakes | 0.389 ± 0.019 | 0.368 ± 0.015 | 0.316 ± 0.016 |
| uncapped stake-weighted log-odds mean, adversary stake 3× | 0.305 ± 0.017 | 0.288 ± 0.020 | 0.270 ± 0.016 |
| skill-weighted trimmed (extension) | 0.313 ± 0.020 | **0.400 ± 0.024** | 0.349 ± 0.018 |

Reference without attackers (E1b, η=0.1): median 0.584 ± 0.022 vs trimmed 0.595 ± 0.025 (CIs overlap).

Overall recall, all bugs:

| aggregator | η=0 | η=0.1 | η=0.3 |
|---|---|---|---|
| median | 0.637 ± 0.006 | 0.581 ± 0.007 | 0.470 ± 0.004 |
| trimmed | 0.645 ± 0.006 | 0.592 ± 0.006 | 0.481 ± 0.007 |
| skill | 0.645 ± 0.006 | 0.610 ± 0.007 | 0.493 ± 0.006 |

**Reading E1:**
- **Trimmed beats median** at every η. CIs do not overlap, and the target-recall gain is about +0.08 to +0.10 absolute.
- **Neither recovers** the attack-free level (about 0.59). Trimming 25% per tail cannot remove a coalition that is 60% of the low tail (deflators plus lazy). It discards honest high reports too, which is why the uncapped log-odds mean does *better* than trimmed when stakes are equal.
- **The stake cap still matters.** Once the adversary posts 3× stake, the uncapped mean falls to trimmed's level and below as η rises. Under the cap, trimmed is invariant to adversary stake by construction (cap = honest stake).
- **Skill weighting helps most** once there is an audit signal (η ≥ 0.1). Weights come from each screener's past audit-set score, which in practice mainly mutes the lazy reporters. This is the best configuration in E1.
- **η costs recall.** With a fixed budget, raising η lowers overall and target recall in every aggregator. In this setting η buys *scoring signal* (no ML payoff at all at η=0), not coverage.
- **Incentives under trimmed, η=0.1** (ML payoff per agent, LOO reference): honest 0.25 ± 0.19, deflator −0.47 ± 0.11, lazy −8.0 ± 0.9. Deviators lose relative to honest.
  - Under the uncapped mean, deflators earn a *positive* payoff (+0.59 ± 0.17 at η=0.1). The reference forecast is itself biased, so being less wrong than the reference pays. LOO only removes self-influence; it does not fix a captured reference.

### E2: ρ_bnd sweep, tilt incentive (analysis Claim 3)
Mix: 20% inflators (report × 1.5), 20% lazy, 60% honest; η=0.3; trimmed aggregator. ML payoff per agent:

| ρ_bnd | honest | inflator | lazy |
|---|---|---|---|
| 0.3 | −0.356 ± 0.013 | **+2.287 ± 0.305** | −29.1 ± 1.4 |
| 0.5 | −0.508 ± 0.017 | +0.174 ± 0.352 | −28.4 ± 1.4 |
| 0.71 | −0.669 ± 0.022 | −2.044 ± 0.413 | −27.8 ± 1.4 |
| 0.9 | −0.814 ± 0.026 | −4.051 ± 0.475 | −27.2 ± 1.4 |
| 1.0 | −0.890 ± 0.028 | −5.108 ± 0.509 | −26.9 ± 1.4 |

**Reading E2:**
- **Down-weighting "safe" resolutions rewards over-reporting risk.** That is Claim 3's tilt, confirmed in simulation. In this setting the crossover sits between ρ_bnd = 0.5 and 0.71.
- **ρ_bnd is not a free knob.** Lowering it to reflect noisy bounded-safe labels makes the scoring rule improper. It must be paired with the per-outcome reweighting in analysis §1.2.
- **Honest payoffs are negative** because the LOO aggregate of the others beats a single honest forecaster. The payoff is relative and roughly zero-sum, so only the honest-vs-deviator *differences* matter.

### E3: Prover tier, mutant kills and invalid certificates
- **Prover mix:** 20% lazy (post BSAFE without searching), 10% cheaters (also post invalid CEX with probability 0.2 per routed task, always caught, bond burned), and one Sybil that clones each kill into 3 identities. The rest are honest.
- **Rewards:** mutant rate 0.3, J = 1, CEX reward 1, bond 1.

Total payoff per prover:

| scheme | honest | Sybil (3 clones) | lazy | cheater |
|---|---|---|---|---|
| 1/n split | 135.3 ± 1.4 | **199.9 ± 5.0** | 15.7 ± 0.6 | 44.7 ± 3.6 |
| geometric J/2^(k−1) | 83.3 ± 0.9 | **41.8 ± 1.3** | 15.7 ± 0.6 | −6.9 ± 3.3 |

**Reading E3:**
- **Geometric decay flips cloning from profitable to unprofitable.** The Sybil goes from 1.48× to 0.50× an honest prover, as the TrueBit argument predicts.
- **Invalid certificates lose money** relative to honest in both schemes. Cheaters also search honestly, so the gap to honest is the cost.
- **Open gap: lazy provers still earn about 19% of honest** (geometric), from unrefuted BSAFE on safe tasks. The window punishes laziness only where bugs exist.

### E4: Sybil self-refutation (accounting check, not an emergent result)
Attacker holds a CEX, posts BSAFE from identity A, and refutes it from B. Refuter bonus R_ref = 0.5; 10% of found CEXs are attacked. Profit per run:
- φ = 1.0 (no burn): +27.1 ± 0.4 at any bond.
- φ = 0.5: bond 0.5 gives +13.6, bond 1.0 gives 0.0, bond 2.0 gives −27.1.

This matches the condition b > R_ref/(1−φ). There must be a burn, and the bond must exceed the refuter bonus divided by the burn share.

### E5: q̂-suppression collusion
Deflating screeners (median aggregator) plus a colluding prover that posts BSAFE on every target task. "Excess" means expected payoff above what the same claim would earn under the honest forecast.

| configuration | colluder profit / task | **excess / task** | buggy-target false-safe survival |
|---|---|---|---|
| no defense | 0.183 ± 0.003 | 0.046 ± 0.001 | 0.313 ± 0.017 |
| skill-trimmed q̂ snapshot | 0.171 ± 0.004 | 0.034 ± 0.001 | 0.220 ± 0.015 |
| snapshot + W_min = 2 | 0.169 ± 0.004 | 0.032 ± 0.001 | 0.202 ± 0.015 |
| snapshot + W_min = 4 | 0.152 ± 0.004 | 0.014 ± 0.001 | 0.057 ± 0.008 |
| snapshot + W_min = 4 + bond 3 | −0.034 ± 0.010 | **−0.001 ± 0.001** | 0.057 ± 0.008 |

**Reading E5:**
- **No single defense is enough.** The snapshot alone removes about a quarter of the excess, and the window floor does most of the work.
- **Only snapshot + window floor + a larger bond** makes suppression unprofitable in this setting (excess ≈ 0).
- **The floor has a cost.** Capital lock-up from a long W_min is not yet modeled.

## Model limits (v0.2)
- One-shot strategies; no adaptive or learning adversaries.
- Refuters are an exogenous hazard λ.
- ML labels on the audit set are "CEX found", so missed bugs count as safe (this is realistic).
- E4 is closed-form accounting.
- Deployer self-dealing and bribery are not yet simulated.
- No capital cost of lock-up.
