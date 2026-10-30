# Related work: two-tier verification market (ML screeners + FV provers)
Protocol Researcher, 2026-10-30 (rev. 2). BibTeX keys refer to `references.bib`.

**Reading depth.** "Full text read" means I read the whole body text (pdftotext / page text), excluding reference lists; appendices noted where skipped. Everything else is marked with what was actually read. Only cite a mechanism detail from an entry marked full text.

| Key | Venue | Depth |
|---|---|---|
| luu2015demystifying | ACM CCS 2015 (ePrint 2015/702) | **full text read** (incl. Appendix A) |
| teutsch2019truebit | arXiv 1908.04756 (whitepaper dated Nov 16, 2017) | **full text read** (incl. Addendum A.1–A.3) |
| alvarez2024bold | arXiv 2404.10491 (Offchain Labs, Apr 15, 2024) | **full text read** (figure-1 diagram text garbled by extraction) |
| wang2024proofphi | arXiv 2404.06495v5 | **full text read of main body (§1–6)**; Appendix A proofs not read |
| sheng2024diligence | AFT 2024, LIPIcs 6:1–6:28 / arXiv 2402.07241v2 | **full text read of main body (§1–7)**; Appendix A (implementation) skimmed |
| solidified_bpm | Solidified blog (Medium), Aug 1, 2018 | **full text read** (via archive.org snapshot) |
| ethresearch_prover_market_proposal / _design | ethresear.ch | substantial excerpts, author/date verified on page |
| arbitrum_bold_docs | Arbitrum docs | overview section |
| kalodner2018arbitrum | USENIX Security 2018 | metadata only |
| canetti2013refereed / canetti2011oneround | Inf. & Comp. 2013 / ePrint 2011/518 | abstract |
| landis2023incentive | arXiv 2312.01549 | abstract |
| lee2025rat | arXiv 2505.24393 | abstract + intro excerpt |
| eip7732 | EIP | abstract |
| hanson2007lmsr | J. Prediction Markets 2007 | abstract + intro |
| carre2021sprig | arXiv 2102.03044v4 (SPRIG whitepaper, Oct 2021) | **full text read** (all 46 pp., incl. Appendices 7–8; figure contents garbled by extraction) |

## 1. The verifier's dilemma

**Luu et al., CCS 2015 (full text).**
- *Threat model.* Miners are ε-rational: they verify a block only if the "advantage" of skipping (Adv(f) = W_f − W_df) is at most εW_blk. Two attacks: (1) *resource exhaustion by problem givers*: because gas fees go only to the block finder, an attacker includes expensive transactions in its own blocks at ~zero net cost, wasting others' verification time (worked example: n=1000 matrix multiplication); (2) *incorrect-transaction attack by provers*: if verification is costly, rational miners skip it, so a wrong result can be accepted. They cite the July 4, 2015 Bitcoin SPV-mining fork as evidence that Nakamoto consensus tolerates unverified blocks.
- *Mechanism.* An "ε-consensus computer": cap total verification work per block at εW_blk, i.e. cap each transaction's gas at G(εW_blk/N₀) (Lemma 1). Larger jobs are handled by (a) *exact* splitting across many transactions (e.g. n² transactions of O(n) work each for matrix multiplication) or (b) *(δ,λ)-approximate verifiability* via property-testing samples (e.g. for sorting, choose k with (1−δ)^{2k} < λ). Case studies: GCD via Bézout coefficients, dot product, sorting, matrix multiplication, 2-colouring. Implementation uses commit-reveal (one transaction commits to another's ID) against a relay/front-running attack, and per-round randomness from SHA256(next block hash ‖ i).
- *Limits stated by authors.* Appendix A: Ethereum's gasLimit can drift ±2⁻¹⁰ per block, so a gas cap is not a full fix. Open problem: incentivising robust verification by changing consensus itself.

**Truebit (Teutsch & Reitwießner; full text).**
- *Assumptions / threat model.* (i) A trusted network (Ethereum) correctly performs tiny computations ("Judges"/"Referees" always adjudicate correctly; censorship of individual transactions assumed away); (ii) all participants, including attackers, are rational with bounded capital; attackers may run arbitrarily many identities (Task Giver, Solver and Verifier simultaneously), pool resources in cartels, and bribe miners to withhold blocks.
- *Dispute layer (verification game).* Solver and Challenger compile Turing-machine tableaus; each round the Solver posts c Merkle roots of equally spaced states, the Challenger names the first index that differs; after log t / log c rounds the Judges check one step from Merkle paths. Judge cost O((log t/log c)(cσ + log c) + 2((2σ+1)log s + 5 + p)). Timeouts = immediate loss. Hash-size σ bounds the largest safely checkable task.
- *Incentive layer (forced errors + jackpot).* Argues "pay for checking" gives no reason to check and "bug bounty" gives no reason to participate if bugs are rare; fix = occasionally *force* the Solver to submit a wrong answer and pay a jackpot to Verifiers who catch it. Parameters: forced-error rate 1/1000 tasks; max jackpot payout = 1/3 of the jackpot repository; verification tax 500%–5000% of task cost, paid by Task Giver into the repository; Solver/Verifier deposits > expected jackpot + cost of a verification game. Randomness = Solver's committed private bits r hashed with the next block hash; Solver commits hashes of a "correct" and an "incorrect" solution before the block hash is known. Verifiers commit challenges as hashes of even integers (odd = camouflage). With k distinct challenges each gets J/2^{k−1} × (task difficulty / max difficulty) — the halving rule is derived so that Sybil-cloning challenges never pays. Unforced error: Verifier wins; Solver pays ≤ ½ deposit to Verifier(s) (refunding Task Giver's taxes from it), rest to repository; losing Verifier forfeits ½ deposit to repository, ½ to Solver.
- *Security argument.* Default Verifier strategy = pick random active tasks; with ≥6 Verifiers per task supported by taxes and attacker ≤1/6 of deposits, P(bogus solution caught) ≥ 1 − (1−1/n)^{5n} > 1 − e⁻⁵ > 99%.
- *Known attacks and patches (Addendum A.1):* premature disclosure of random bits (penalty: ½ Solver deposit burned, ½ to reporter); incorrect secondary solution (Verifiers commit mod-3 to challenge A, B or both); program abort (explicit step bound); "jackpot balloon" (fixed absolute payout cap); incentivised block withholding (deterred if premature-reveal penalty > expected jackpot × forced-error probability). The authors call forced errors TrueBit's "Achilles' heel."

**Proof of Diligence (Sheng et al., AFT 2024; full text main body).**
- *Model.* n watchtowers with relative stake α_i (Σα_i = 1, total stake S), rational, computationally bounded; L1 secure and live; data available. Threats: lazy watchtowers and collusion (static adversary; adaptive adversary only under "rational independence" + private whistleblower assumptions).
- *Proof of diligence.* Each watchtower executes the batch to get state root r_S′ and execution-trace root r_E (only obtainable by executing), then computes (d, π) = VRF_sk(r_S′ ‖ r_E). It wins a bounty if d < φ(α_i) = 1 − (1−θ)^{α_i}. Other watchtowers recompute and can challenge within t_C via a `validate` (L1 re-execution or interactive game).
- *Payoffs.* Bounty R_B per winner, challenge reward R_C, dispute cost c_V, execution cost c_T. Conditions: R_B > c_T/φ(α₀), R_C > c_T, α₀S ≥ c_V + (n−1)R_C. Theorem 1: diligence is a dominant strategy, unique NE. But with smart-contract-enforced *lazy collusion* (all agree on a fake r_E′ with deposit t) a second, Pareto-better all-lazy NE exists (Cor. 4/6). Fix: a whistleblower bounty R_w > φ(α_i)R_B + c_V + α_iSφ(α_i) + c_T makes the all-diligent NE unique (Cor. 8).
- *Numbers.* With c_T=1, n=10, θ=0.9: φ≈0.2, R_B>5, R_C>1, α₀S>100,009 (c_V=100,000), R_w>120,572; n=100 → R_B≥44, R_w>102,281. Deployment: 10 EigenLayer operators using restaked ETH, watching OP-Goerli and Base-Goerli; bounty transaction ≈380K gas; slashing goes through EigenLayer's slasher contract (App. A).

- **Landis 2023** (abstract only): formally models incentive failure of optimistic rollups when fraud never occurs.
- **RAT (Lee & Bak 2025)** (abstract + intro): randomized L1 attention tests on validators; reports an equilibrium with small penalties and under 1% test frequency.

**Relation to our design.** Our setting has the dilemma twice: (a) bounded "safe" FV claims that no one ever refutes, (b) screeners who earn nothing if no bug surfaces. Truebit's forced errors and PoD's VRF bounty mining are the two concrete templates for "paying for attention when faults are rare": Truebit manufactures faults (needs unpredictable randomness and a large jackpot repository funded by a 5–50× tax), PoD pays for a *proof of having done the work* (needs work whose output is deterministic and recomputable by peers). Neither transfers directly: FV runs are not deterministic proofs of work (solver nondeterminism, timeouts), and forced bugs in real contracts would mean planting vulnerabilities. Our proper-scoring-rule payment to screeners gives a reward stream that does not depend on fraud occurring; PoD's collusion result (lazy-collusion NE needs a whistleblower) is a warning that applies to screeners copying one shared model.

**Gap.** All of this targets *deterministic re-execution*, where one honest checker settles truth cheaply (Luu's ε bound, Truebit's single-step Judge check, PoD's recomputed r_E). EVM safety properties are undecidable in general, "safe" claims are bounded, and ground truth arrives late and one-sidedly (counterexample, exploit, audit).

## 2. Challenge and refutation games
- **Refereed delegation (Canetti, Riva & Rothblum)** (abstract): correct answer recovered if ≥1 of several servers is honest; log rounds, collision-resistant hashing. Truebit states its game is "essentially due to" this work.
- **Arbitrum (Kalodner et al. 2018)** (metadata only): original bisection dispute design.
- **SPRIG (Carré, Gabriel, Hongler, Lacerda & Capano 2021; full text).** A recursive claim/question debate over *mathematical* proofs: a claimer posts a hierarchical proof sketch of level L with a stake pair (σ↑, σ↓); any skeptic may pay a bounty β to question one sub-statement, which must be answered within τ by a level-(L−1) claim, and so on down to a level-0 machine-checkable proof that a contract verifies automatically (computation cost c₀ burnt). An unanswered question invalidates its claim (σ↑ to the originating question, σ↓ to the first defeating question); the first validated answer collects the question's bounty. It analyses attacks (carpet-bomber, nitpicker, evasive prover, sandbagger, plagiarist) and a two-level signaling game with a unique Perfect Bayesian Equilibrium, showing that stakes too low to make challenging worthwhile give a no-challenge equilibrium in which acceptance is uninformative (Type-I error ½). It even proposes security-audit bounties (§5.3) and derivative markets on outcomes (§5.5).
  *Relation:* closest prior design for *∀-claims settled by a machine checker*, but its burden is on the claimer to unroll proofs on demand, and it has no ML/forecast tier.
- **BoLD (Alvarez et al. 2024; full text).**
  - *Threat model.* L1 is live and safe, at least one honest party; adversary may censor honest transactions for at most C_max rounds in aggregate (conservatively ~1 week on Ethereum), order transactions, attempt resource exhaustion and delay attacks. Nominal delay δ per move.
  - *Problem with Arbitrum Classic.* Two-party chess-clock challenges; under partial concurrency an attacker with N stakes can delay ≈2N challenge periods (N−1 confederates lose slowly), which is why Classic was permissioned.
  - *Mechanism.* Assertions commit to the whole execution history (Merkle tree of all states), so there is one justifiable bisection at each step and honest parties cooperate trustlessly ("trustless cooperation"): the correct assertion need be staked only once. All assertions/bisections form a DAG; each node has a local timer that runs while it is *unrivaled*; bottom-up timer = own timer + min over children (max over refinement children in multi-level). A root is confirmed when its bottom-up timer ≥ T. Corollary 1: if T > C_max + (δ+1)(k_max+2), the honest root wins by round T + C_max + (δ+1)(k_max+2) (plus (δ+1)(k_max+1) for lazy updates), i.e. about two challenge periods regardless of the number of adversarial assertions N_A.
  - *Multi-level.* Recursive refinement over strides Δ_ℓ (e.g. n=2⁵⁵ split as 2³⁰ coarse × 2²⁵ fine; implementation uses L=3) cuts off-chain hashing; stakes are required at each level.
  - *Payoffs.* Fixed stake S per root, losers' stakes confiscated to reimburse honest gas: S ≥ k_max·G_bisect + G_proof + (k_max+1)·G_update. Resource ("griefing") ratio R = (G_A+S_A)/G_H can be pushed to any ρ by raising S; multi-level needs stakes growing geometrically (ρ^L·γ) for ρ>1, or linearly for ρ=1. A "cohort" stake (S × cohort size) gives an asymptotically unbounded ratio. Comparison: Cartesi tournaments take T(1+⌈log₂(1+N_A)⌉) but cost honest parties only log N_A.
  - *Docs.* The Arbitrum docs overview adds deployment detail (bounded dispute time plus a Security Council grace period; permissionless validation).

**Relation to our design.** Tier 2's strongest artifacts avoid bisection: a counterexample is a replayable EVM trace, checkable in one shot. Our refutation window is one-sided — anyone may post a counterexample against a bounded "safe" claim — like a BoLD challenge whose evidence is a complete witness. BoLD's key transferable ideas: (1) claims not tied to who staked them, so any honest party defends the truth; (2) timers that run only while unrivaled, giving a principled window length T > C_max + (moves × delay); (3) stake sizing from a target griefing ratio.

**Gap.** Fraud-proof games settle a *computation's output*; ours settle ∀-claims where only the ∃-side has a cheap witness. Our reward decay keyed to ML p_bug has no counterpart in what we read. Also, checking is ≥10× faster than solving for only ~4% of Carcara proofs (per the brief), whereas BoLD/Truebit assume one-step checks are trivially cheap.

## 3. Proof markets and prover networks
- **Proofφ (Wang et al.; full text main body).**
  - *Model.* Per-round auction per task type; users bid fee f; provers bid (capacity s, unit cost p); a trusted coordinator (e.g. a rollup sequencer) runs it; parties myopic; *risk-averse* (deviate only if certainly profitable).
  - *Core mechanism.* Sort fees descending, costs ascending; ℓ = max j with p_{j+1} ≤ f_{S̄_j+1}; allocate the first ℓ provers in full with the top S̄_ℓ tasks; every user pays f_{S̄_ℓ+1}; each allocated prover gets s_j·p_{ℓ+1}. Proven budget balanced and DSIC for users and provers (on cost, not capacity).
  - *System layer.* Collateral ≥ p̄·s (p̄ = public refund cap), seized for missing/incorrect proofs and paid out as refunds; capacity misreporting shown profitable only for specific bid profiles → fix capacity for several rounds; user-Sybil and collusion deviations profitable only with knowledge of others' bids → sealed (encrypted) bids; prover-Sybil splitting profitable only if it raises welfare. Full monopoly collusion not handled.
- **ethresear.ch, "An Ethereum Prover Market Proposal" (Julian, Jul 29, 2025)** (excerpts): builders deposit prizes into a system contract, any prover may claim a share in the next slot, attesters enforce payment; no relays, no prover stake.
- **ethresear.ch, "On Ethereum Prover Market Design" (maryam & mike [neuder], Aug 13, 2025)** (excerpts): compares proof lotteries vs staked allocations; asks whether a decentralized prover market is needed at all.

**Relation to our design.** These markets buy proofs of statements known to be provable; only price and liveness matter, and Proofφ assumes known per-task cost p. Tier 2 buys answers to open questions with unknown, possibly unbounded cost; our ML-routed budget plays the role of the prize deposit but must allocate under uncertain value. Proofφ's techniques (collateral = refund cap × capacity, sealed bids against Sybil/collusion, multi-round capacity lock-in) are directly reusable for the Router.

**Gap.** No proof market we read prices *risk information* (Tier 1) or uses one tier's forecasts to route another tier's work.

## 4. Verifier networks, watchtowers, information markets
- PoD and RAT (§1) are the closest staked, monitored, paid-for-diligence verifier networks.
- **Hanson LMSR (2007)** (abstract + intro): market scoring rules elicit consensus probabilities; logarithmic versions preserve conditional independence — supports the brief's optional combinatorial LMSR.
- **Solidified bug prediction market (Munoz-McDonald, Aug 1, 2018; full text).** Per-contract market tied to deployed bytecode with an end date; "bug" and "bug-free" outcome tokens each pay 1 SOLID; the market creator supplies liquidity that funds an automated market maker; built on Gnosis prediction-market contracts. Bug hunters can buy "bug" tokens and then report the bug. Resolution initially by Solidified's centralized Bug Verification Oracle (decentralization planned per their whitepaper §4.6, not read); Augur rejected as oracle because bug validity is ambiguous. Claims insider trading is not a concern because the code is immutable. **Closest prior concept to Tier 1.**

**Gap.** Solidified resolves by a centralized human oracle and has no FV tier. We add: (1) machine-checkable resolution (counterexamples/certificates); (2) screeners as calibrated models scored per property by a proper scoring rule, not traders; (3) prices steer verification effort, creating a routing-manipulation incentive absent from a stand-alone market. Note Solidified's "buy bug tokens then report" is exactly the insider profit route we must analyse for screeners who also act as provers.

## 5. Closest prior work, ranked
1. Solidified bug prediction market — same object, no FV, no routing.
2. PoD, Truebit (forced errors), RAT — attention incentives when faults are rare.
3. BoLD, refereed delegation — refutation-window semantics, window length, stake sizing.
4. Proofφ, ethresear.ch prover markets — market mechanics for paid verification work.
5. Luu et al. — the underlying incentive problem.

## 6. Gaps the two-tier market fills (candidate contributions)
- **G1.** Incentives for *undecidable ∀-properties* with delayed, one-sided ground truth (prior work assumes deterministic re-execution).
- **G2.** *Counterexample-first slashing*: immediate slashing for checkable artifacts, decaying rewards for bounded "safe" claims.
- **G3.** *Forecast-routed verification budgets* robust to manipulation.
- **G4.** A screener reward stream independent of fraud occurring (proper scoring rule), as an alternative to Truebit's forced errors / PoD's bounty mining.
- **G5.** Checking cost close to solving cost (Carcara data), unlike fraud-proof literature.

## 7. To read next (not cited for any claim yet)
- Kalodner et al. 2018 full text; Canetti–Riva–Rothblum full text; Landis 2023 and RAT full text.
- Proper-scoring-rule / peer-prediction literature.
- Ed Felten's "cheater-checking problem" post (linked from ethresear.ch topic 8590; not fetched).
- OP Stack fault-proof spec (removed from bib: only page headings were read).
- EigenLayer's own whitepaper (not obtained; see placement-sketch).
