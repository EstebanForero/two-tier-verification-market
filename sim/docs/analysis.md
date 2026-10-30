# Incentive, collusion and routing-manipulation analysis

Draft v0.1. Proof sketches, not full proofs. Assumptions labelled A1…; numbers labelled *illustrative*.

**Assumptions.** A1 risk-neutral, profit-maximising agents (as in TrueBit §2.2(ii)). A2 the reference EVM replay and certificate checkers are correct (analogue of TrueBit's "Judges adjudicate correctly"). A3 the randomness beacon is unpredictable before reveal and not biasable more cheaply than the value at stake. A4 L1 censorship of single transactions over a window of Δ blocks is negligible. A5 ground truth, *when it resolves*, is correct up to ρ (audits/bounded claims are noisy).

## 1. Incentive compatibility of ML reporting

### 1.1 Baseline (full, immediate resolution)
**Claim 1.** With a strictly proper S, payoff α·[S(p,Y) − S(r,Y)] where r does not depend on i's report, truthful p = belief q maximises expected payoff uniquely.
*Sketch.* E_q[S(p,Y)] ≤ E_q[S(q,Y)] with equality iff p=q (strict propriety, Gneiting & Raftery 2007, eq. (1)); subtracting h(Y)=S(r,Y) and scaling by α>0 preserves this (their eq. (2)). Caveat: r must be computed *without* i's report (leave-one-out), else i influences its own baseline.

### 1.2 Partial and selection-biased resolution
Let R ∈ {0,1} indicate resolution, P(R=1 | x) = π_x·d_x + (1−π_x)·e_x, where d_x is the resolution chance if routed and e_x via exploit/audit otherwise.

**Claim 2 (resolution independent of Y given report ⇒ still proper).** If P(R=1 | Y, p) does not depend on Y, expected payoff is P(R=1)·E[ΔS], so maximisation is unchanged for any P(R=1)>0 not controlled by i.

**Claim 3 (the problem).** Resolution *is* correlated with Y: bugs are resolved (CEX, exploit) much more often than safety (BSAFE only gives ρ_bnd<1; most clean contracts never get UCERT). Then the effective distribution screeners are scored against is P(Y | R=1) ≠ P(Y). With ρ-weighted partial resolution, an agent with belief q maximises
  E[ρ·w·S(p,Y)] ∝ q·r1·S(p,1) + (1−q)·r0·S(p,0),  r_y = E[ρ·w·1{R=1} | Y=y].
For a proper S the optimum is the *tilted* belief p* = q·r1 / (q·r1 + (1−q)·r0). If r1 > r0 screeners over-report risk. *Sketch*: the expression is the expected score under the reweighted distribution q', and propriety gives p*=q'.
**Fix.** Choose weights so r1 = r0 — i.e. importance-weight by inverse resolution probability *per outcome class*. This needs an estimate of P(R=1|Y), which we only get on the **random-audit subset** (η-share routed uniformly, then pushed to full resolution: UCERT attempt + audit). Practical rule: score ML **only** on the random-audit subset with w=1/η (unbiased, high variance), plus a low-weight term on the routed subset; this is the standard "explore share" fix. Variance cost ∝ 1/η — simulation question.

**Claim 4 (routing feedback).** If i's report changes π_x and hence R, i gains an extra lever: deflate p on tasks where it believes q high but fears being shown wrong? No — under IPW with w=1/π_x the expected weight E[w·1{routed}] = 1 regardless of π_x, so the IPW-weighted score is invariant to i's effect on π_x (sketch: E[1{a=1}/π] = 1). Requires π_x > 0 always ⇒ the η floor is *necessary* for propriety under routing, not just helpful. Residual: variance of w when π small; clip w at w_max (introduces bias ~ mass of π<1/w_max).

### 1.3 Delay and stakes
Discount factor δ per epoch and stake opportunity cost r: payoff δ^τ·E[ΔS] − r·s·τ. Scaling by a positive constant keeps propriety, so **delay does not distort reports, it reduces participation** (individual rationality: need α·E[ΔS_skill]·δ^τ > r·s·τ + cost of model). Risk aversion *does* distort (pulls reports toward the reference); bounded Brier is less exposed than log. Use Brier by default; log score's unboundedness (G&R §3) also makes stake sizing impossible without clipping.

### 1.4 Window length (CFRW)
Detection-hazard model: bug present with prob q̂, refuter finds CEX at rate λ. Social value of window W: q̂·v·(1−e^{−λW}) − b·r·W. Optimum W* = (1/λ)·ln(q̂·v·λ/(b·r)) when positive — W grows (log) in q̂, matching W(q̂) increasing in model.md §4.1. *Illustrative only*; λ must be measured from the Verification Researcher's Halmos/hevm mutant runs.

## 2. Collusion
### 2.1 ML–FV collusion
- **Deflate-and-certify**: screeners lower q̂ on x; colluding prover posts BSAFE, collects P_safe ∝ (1−q̂)^θ. Gain ΔP ≈ β_safe·v·θ·Δq̂. Cost: if a bug exists (prob q), screeners lose α·[S(q,1)−S(q−Δ,1)] ≈ 2αqΔ (Brier, small Δ) per task; prover loses b if refuted in window. Attack unprofitable if β_safe·v·θ·Δ < q·(2α·n_col·Δ + b·(1−e^{−λW})) roughly. Cheap fix: **freeze q̂ before routing and use only the random-audit-calibrated q̂** for decay; or make P_safe depend on q̂ computed *excluding* the top-ω weight holders.
- **Inflate-to-attract**: screeners raise q̂ to steer budget to tasks where an allied prover already holds a CEX (or a mutant leak). Profit = P(x) for the allied CEX. Cost = Brier loss if actually safe. Defense: CEX rewards don't require routing (anyone can refute), so routing matters only for *budget subsidy*, not for the right to be paid for a CEX → decouple CEX bounty from routing.

### 2.2 Sybils
- ML: proper scoring is linear in stake per report; splitting stake across Sybils gives no score advantage *if* aggregation weight is capped per **stake**, not per identity. Caps per identity (ω_max) are Sybil-defeated; so cap per stake-unit + require minimum coverage n_min per identity.
- FV mutant split 1/n_m: a Sybil that duplicates its own kill gets the same total (n identities × 1/(n+others)) — actually *increases* share against honest co-killers: with o honest killers, one identity gets 1/(1+o), s Sybils get s/(s+o) > 1/(1+o). **This is a real hole.** Fix: TrueBit's geometric decay — total payout on a mutant with k killers ≤ J/2^{k−1} (Teutsch & Reitwießner §5.3, proven there to make cloning unprofitable), or require a unique bond per kill ≥ marginal gain.

### 2.3 Withholding counterexamples
A prover who finds a real CEX may withhold it to (a) sell to the deployer / exploit, (b) wait until a BSAFE by a rival is posted to also collect φ·b. (b) is *intended* — it raises the cost of false safe claims. (a) is bounded by bounty vs exploit value: no in-protocol bounty can beat v_exploit for high-TVL contracts (same point as TrueBit §5.2 "no penalty scheme can deter all such attacks"). State as a limitation; bounty β_CEX·v_x should scale with TVL.

### 2.4 Self-dealing with deployers
Deployer wants a cheap "safe" signal. Paths: (i) post own contract, run own Sybil screeners at low q̂, Sybil prover BSAFE. Defense: BSAFE never yields a "certified" label; window length floor; randomised η share means an outsider prover may be routed to it anyway. (ii) Deployer bribes refuters to stay silent: bribe must exceed φ·b + P(x) for *every* potential refuter — scales with number of independent refuters, fine if the refuter pool is large (assumption, to be simulated).
(iii) Deployer submits contract with planted, known bug to farm mutant-style rewards: real-bug rewards come from a deployer-paid fee pool, so self-farming is circular (pays itself minus burn) — unprofitable if burn > 0.

### 2.5 Mutant leakage
Mutants must be indistinguishable from real code and their identity hidden until after claims (TrueBit forced errors §4.4). If a deployer/screener learns which are mutants, unique-kill weighting can be farmed. Commit-reveal of the mutant seed with a beacon; mutant identity revealed only at settle.

## 3. Hardness of routing manipulation
Adversary controls stake fraction f of the capped aggregation weight and wants to move π_x by Δπ on a target set T.
- Effect on q̂ of a trimmed, capped log-odds mean: |Δ logit q̂| ≤ f·L/(1−trim) where L is max report logit. Then |Δπ_x| ≤ (1−η)·|∂g/∂q̂|·|Δq̂| / Σg, and floor π_x ≥ η/|X|.
- **Deflection** (keep FV away from x): best the adversary can do is π_x → η/|X| (exploration floor). Probability x is still examined over E epochs ≥ 1 − (1−η/|X|)^E. Like TrueBit's 1 − (1−1/n)^{5n} > 99% argument, coverage comes from *independent random* checking, not from honest scores.
- **Cost of attack** per epoch on |T| tasks: expected Brier loss ≈ α·Σ_{x∈T} (p_x − q_x)² (for Brier, expected loss of reporting p under truth q equals (p−q)², the Bregman divergence, G&R Example 1) plus forgone honest reward. **Profit**: deflection value = v_exploit·P(bug found by FV | routed)·Δπ. So manipulation is unprofitable when α·(Δp)² > v_exploit·d·Δπ. Because the cost is *quadratic* in the distortion and the routing effect is *linear*, small distortions are always cheap ⇒ proper scoring alone cannot stop routing manipulation for high-value targets; **the η floor and stake-weight cap carry the security**, scoring merely keeps it expensive to be large-scale wrong.
- **Inflation** (pull FV to decoy tasks to starve others): bounded by the same cap; also self-defeating if FV finds nothing (screener loses). Starvation of a target is bounded by budget share η.

Proposed fixes (summary): (1) random audit routing share η with recorded π and IPW scoring; (2) per-stake influence cap ω_max and trimmed aggregation; (3) commit-reveal of ML reports, prover claims, and refutation CEXs, beacon after reveal; (4) q̂ snapshot frozen before BSAFE; (5) geometric decay for duplicate kills; (6) bond burn share (1−φ) on every slash; (7) CEX bounties independent of routing; (8) window extension on late commits.

## v0.2 simulation evidence (see results_v02.md; illustrative parameters)
- Claim 3's tilt is reproduced: at ρ_bnd ≤ 0.5, inflators out-earn honest screeners. ρ_bnd must be paired with per-outcome reweighting.
- §2.2's Sybil hole under 1/n is reproduced (1.48× honest). Geometric decay closes it (0.50×).
- §3: a 60% low-side coalition (deflators + lazy) defeats both median and 25% trimming. Trimmed beats median by about 0.1 target recall but stays well below the no-attack level. Skill weighting from the audit set is the strongest fix tested, which strengthens the case for η > 0 as a *signal* source.
- LOO removes self-influence, but a captured reference still lets deflators earn positive relative scores (uncapped mean). Propriety relative to the reference needs an honest-majority reference.

## References (read via WebFetch on Oct 30, 2026)
- T. Gneiting, A. E. Raftery. Strictly Proper Scoring Rules, Prediction, and Estimation. JASA 102(477), 2007. https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf
- J. Teutsch, C. Reitwießner. A scalable verification solution for blockchains (TrueBit), 2017. https://arxiv.org/abs/1908.04756
- ethereum.org. Optimistic Rollups (challenge period, bond slashing/burn, bisection). https://ethereum.org/en/developers/docs/scaling/optimistic-rollups/
Not read (fetch failed): peer-prediction literature — not cited; see open_questions.md.
