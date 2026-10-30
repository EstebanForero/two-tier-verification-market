# Simulation plan (Python agent-based)

## Skeleton (exists, runnable)
`sim/sim.py` (numpy only): `python3 sim/sim.py`; output from first run saved in `sim/run_output.txt`. It covers ML screeners only (honest, lazy, adversarial deflators), median aggregation, η-exploration routing, FV detection modelled as a Bernoulli event, and Brier scoring on a uniform audit subset.

**First-run observations (illustrative parameters, 1 seed, not results):**
- With 40% deflators plus 20% lazy reporters, the median aggregate is captured. Recall on targeted tasks falls from about 0.52 to about 0.31.
- Raising η to 0.3 barely restores target recall (≈0.28 against 0.40 overall). Because the budget is fixed, more exploration also lowers overall recall (0.52 → 0.40).
- Lazy base-rate reporters are heavily penalized, as intended. Adversaries lose more than honest screeners, but only slightly: the loss is quadratic, so it is cheap, which matches analysis §3.
- Honest payoffs are slightly negative because the reference forecast includes their own report. A leave-one-out reference is required (analysis §1.1). Fix this in v0.2.

## v0.2 (built)
`sim/v02/core.py` and `sim/v02/experiments.py` implement:
- the prover tier (honest, lazy, cheater, Sybil; mutant kills with 1/n or geometric rewards; invalid-certificate slashing)
- the CFRW window W(q̂) with W_min, bond, φ burn, and refuter bonus
- Sybil self-refutation (E4) and q̂-suppression collusion with snapshot/W_min/bond defenses (E5)
- leave-one-out reference
- aggregators: median, stake-capped trimmed, uncapped weighted mean, skill-weighted trimmed
- 30-seed t-based 95% CIs

Results are in `results_v02.md`. Not yet built: deployer agents, adaptive adversaries, capital lock-up costs, the commit-reveal/beacon layer (assumed ideal).

## Target module layout
```
sim/
  agents.py    # HonestML, LazyML, AdversarialML(deflate/inflate targets), ColludingML+Prover, HonestProver, LazyProver(BSAFE spam), Refuter, Deployer(self-dealing), Sybil wrapper
  world.py     # contract/task generator: base rate, TVL v_x, bug detectability λ_x, mutants
  scoring.py   # Brier/log/spherical, leave-one-out reference, IPW weights, ρ partial resolution
  routing.py   # g(q̂,v), η floor, stake caps ω_max, trimmed aggregation, beacon
  window.py    # CFRW: W(q̂), refutation hazard, late-commit extension, clawback
  ledger.py    # stakes, bonds, slashes, burns, vesting
  market.py    # epoch loop: commit→reveal→route→prove→window→settle
  experiments.py / run.py  # sweeps, seeds, CSV output
```

## Agent types
| Agent | Behaviour |
|---|---|
| Honest ML | reports a noisy belief, quality parameter σ |
| Lazy ML | reports the base rate or copies the previous aggregate |
| Adversarial ML | deflates or inflates on a target set T by a factor; stake fraction f |
| Colluding ML+FV | deflates, then the partner posts BSAFE (analysis §2.1) |
| Honest prover | searches routed tasks for CEX; posts UCERT/BSAFE when the search fails |
| Lazy prover | posts BSAFE without searching |
| Refuter | searches tasks with open windows; hazard λ |
| Sybil | splits identity to farm duplicate-kill splits |
| Deployer | self-deals, bribes refuters, plants bugs |

## Parameters (sweep ranges illustrative)
base rate 0.02–0.2; n_ml 10–100; adversarial stake fraction f 0–0.6; η 0–0.4; FV budget 5–30% of tasks; detect 0.3–0.95; W_0, κ_W; bond b; burn share 1−φ; θ (decay); ρ_bnd 0.3–0.9; ω_max; seeds ≥ 30.

## Metrics
Bug recall overall and on the target set; FV budget efficiency (bugs per unit of budget); ML calibration (reliability and Brier skill on the audit set); profit per agent type (IC check: does any deviation beat honest?); false-safe rate (BSAFE on buggy tasks that survive the window); capital lock-up; variance of IPW payoffs.

## Experiments
- E1 propriety under selection bias: IPW vs naive scoring; measure tilt p* − q (analysis Claim 3).
- E2 routing manipulation: f × η × aggregator (mean, median, trimmed, stake-capped) → target recall, attacker profit.
- E3 CFRW: W, b, φ, θ → false-safe rate, lazy-prover profit, collusion profit (§2.1, G3).
- E4 Sybil duplicate kills: 1/n vs geometric decay.
- E5 lazy provers vs mutant injection density.
- E6 deployer self-dealing and bribery vs size of the refuter pool.
