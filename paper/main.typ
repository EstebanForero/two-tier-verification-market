#set document(title: "A Two-Tier Verification Market for EVM Bytecode", author: "Esteban Fernando Forero Montejo")
#set page(paper: "us-letter", margin: 1in, numbering: "1")
#set text(font: "New Computer Modern", size: 10.5pt)
#set heading(numbering: "1.1")
#set math.equation(numbering: "(1)")
#set par(justify: true)
#let todo(body) = text(fill: red)[[TODO: #body]]

#align(center)[
  #text(16pt, weight: "bold")[A Two-Tier Verification Market for EVM Bytecode:\ ML Screening Meets Certificate-Backed Formal Verification]
  #v(4pt) Esteban Fernando Forero Montejo
]

#heading(outlined: false, numbering: none)[Abstract]
#todo[Write after results. One paragraph: problem, two-tier mechanism, counterexample-first slashing, manipulation-resistant routing, evaluation summary.]

= Introduction
Smart contracts on Ethereum hold significant value, yet verifying their bytecode remains expensive. Machine-learning vulnerability detectors are cheap and scale to every deployed contract, but their outputs are probabilistic and cannot be trusted on their own. Formal verification (FV) gives strong guarantees, but it is costly, so it can only be applied to a small fraction of contracts and properties. #todo[cite ML detectors and FV tools from related-work folder]

We propose a two-tier verification market that combines the two. In the first tier, staked ML _screeners_ publish calibrated risk probabilities for each contract and property. They are paid through a proper scoring rule that settles later against ground truth, such as an FV counterexample, an observed exploit, or an audit finding. In the second tier, FV _provers_ submit checkable certificates. The screeners' scores decide how a fixed FV budget is routed across contracts and properties.

The central difficulty is that the parties being paid are not equally easy to check. A counterexample is a replayable EVM trace, and a checkable unbounded certificate (for example, a constrained-Horn-clause invariant) can be validated directly. Both can therefore be slashed immediately if they are invalid. Bounded or "safe" claims cannot be refuted this cheaply. We pay them through a refutation window, with a reward that decays as the screeners' bug probability rises, so a prover gains more from finding a counterexample than from claiming safety. We call this _counterexample-first slashing_. The asymmetry matters in practice: checking a proof is at least ten times faster than solving the problem in only about 4% of the 39,229 proofs in the Carcara corpus, and the Alethe proof format does not support arrays. #todo[cite Carcara/Alethe]

== Problem Statement
Given a set of contracts, a set of properties per contract, and a fixed FV budget, we want to design a mechanism that:
+ elicits truthful, calibrated risk estimates from ML screeners;
+ routes the FV budget toward high-risk contract–property pairs without letting screeners steer provers by inflating or deflating their scores;
+ pays provers only for claims that are, or can become, checkable, and slashes them for invalid ones; and
+ discourages lazy provers and colluding screener–prover pairs.

== Contributions
#todo[Finalize with Ideation Agent and Lead Researcher.]
- A two-tier market design linking scoring-rule-paid ML screeners to certificate-backed FV provers.
- Counterexample-first slashing with refutation windows for claims that cannot be checked directly.
- An analysis of manipulation-resistant routing and collusion. #todo[Mechanism Designer]
- A laptop-scale prototype and evaluation on EVM benchmarks. #todo[Verification Researcher]

= Related Work
// Read depth is limited: every source below has so far been read only at the abstract, excerpt, or metadata level. Specific claims are marked TODO until the full text has been checked.

*The verifier's dilemma.* Luu et al. named the _verifier's dilemma_: when checking is costly, rational participants may accept results without validating them @luu2015demystifying. Truebit adds an incentive layer around an interactive verification game @teutsch2019truebit #todo[confirm forced-error/jackpot details from the full text]. For optimistic rollups, Landis models how incentives break down when fraud never occurs @landis2023incentive, while Proof of Diligence @sheng2024diligence and RAT @lee2025rat require watchers to keep showing that they are actually verifying. #todo[state their security assumptions and equilibrium numbers only after reading the full text] Our design faces the same dilemma twice: for "safe" claims that nobody refutes, and for screeners when bugs never surface. Paying screeners for calibration through a proper scoring rule gives them a reward stream that does not depend on fraud occurring.

*Challenge and refutation games.* Refereed delegation shows how a client can obtain a correct answer as long as one of several servers is honest @canetti2013refereed @canetti2011oneround, and it underlies the bisection fraud proofs of Arbitrum @kalodner2018arbitrum, BoLD @alvarez2024bold @arbitrum_bold_docs, and the OP Stack @optimism_fault_proofs. #todo[BoLD delay bounds and OP Stack details pending full read] These games settle disputes about the output of a _deterministic computation_. We instead settle claims about _all_ executions of a contract, where only the existential side, a counterexample, has a cheap complete witness. Our refutation window is therefore one-sided. We borrow BoLD's principle that the outcome should not depend on who bonded the claim. #todo[verify this principle in the BoLD paper]

*Proof markets.* Proof$phi$ proposes an incentive-compatible auction for zero-knowledge proof generation @wang2024proofphi, and Ethereum researchers have discussed L1 prover markets @ethresearch_prover_market_proposal @ethresearch_prover_market_design. #todo[specifics of Proof$phi$ collusion handling and the ethresear.ch designs pending full read and author verification] These markets buy proofs of statements already known to be valid. Tier 2 buys answers to open questions whose cost is unknown and may be unbounded, and no prover market we know of uses forecasts from one tier to route the work of another.

*Information markets.* Hanson's logarithmic market scoring rule @hanson2007lmsr motivates our optional combinatorial market over correlated properties. The closest prior concept to Tier 1 is the Solidified bug prediction market @solidified_bpm, which trades bug and bug-free outcome tokens for contract bytecode #todo[grey literature; verify date and resolution process]. Our design differs in three ways: resolution is machine-checkable, screeners are calibrated models scored per property, and prices steer verification effort, which introduces a routing-manipulation incentive that a stand-alone market does not have.

*Gaps.* Taken together, prior work does not address (i) incentives for verifying undecidable universal properties against delayed, one-sided ground truth; (ii) slashing that separates checkable artifacts from bounded claims; (iii) forecast-routed verification budgets; or (iv) settings where checking costs approach solving costs. #todo[cite Carcara data source]

= Model
== System Placement
We place the market at the application layer as a contract-level escrow on Ethereum, with four components:
- `MarketEscrow` holds the bounty pool and the stakes of screeners and provers.
- `ScreenerBook` records commit-reveal risk probabilities per (code hash, property) and settles them against a resolution oracle.
- `ProverRegistry` accepts certificates. Counterexamples are replayable EVM traces checked by on-chain or optimistic re-execution. Invariant certificates are checked off-chain and backed by a single-witness challenge game. Bounded "safe" claims open a refutation window.
- `Router` allocates the fixed FV budget from the revealed scores and adds randomized spot checks.

*Trust and threats.* Counterexamples are trust-free, but audit and exploit outcomes require a resolution oracle, which we model as an explicit committee. Liveness requires at least one honest challenger per window, and we use attention-test ideas to address the verifier's dilemma @lee2025rat @sheng2024diligence. Certificate checking on-chain is likely infeasible, so it happens off-chain. Front-running of counterexamples and score reveals is countered by commit-reveal schemes bound to the submitter's address.

*Why not enshrine it?* A protocol-level market, along the lines of L1 prover-market proposals @ethresearch_prover_market_proposal and builder payment plumbing in the style of EIP-7732 @eip7732, would give the strongest payment guarantees. We reject it for three reasons: contract safety is not a consensus-validity condition, ground truth arrives late and through an oracle, and FV jobs do not fit slot timing. We return to it in @sec-discussion for zkVM circuits.

#todo[Agents, contracts/properties, ground-truth oracle, certificate types and checking costs.]

= Mechanism
== Tier 1: ML Screeners and Proper Scoring
== Tier 2: FV Provers and Counterexample-First Slashing
== Budget Routing
== Optional Extensions
#todo[Combinatorial LMSR over correlated properties; anti-laziness spot checks.]

= Dataset <sec-dataset>
// Outline from PLAN.md Stage 1. Numbers are targets, not results.
#todo[Fill in when Stage 1 (Dataset v1) exits.]
== Sources
- *SmartBugs Curated:* about 143 contracts across the DASP categories, pinned by commit and compiled per contract with a pinned `solc` to runtime bytecode and a CFG. #todo[cite SmartBugs, DASP]
- *Mutants:* injected with SuMo/Gambit-style operators (reentrancy, unchecked call, removed access control, arithmetic, `tx.origin`), with seeds. For each mutant we record the operator, its location, and whether a Halmos property kills it. #todo[cite SuMo, Gambit, Halmos]
- *Real labels:* DeFiHackLabs reproductions, SolidiFI, and Web3Bugs/Code4rena findings (license-checked). #todo[cite]
- *Presumed-safe set:* audited, long-lived, high-TVL contracts. These labels are one-sided, and we state that caveat explicitly.
== Properties
Each contract gets property templates written as Halmos `check_` functions: no-drain, withdrawal always possible, owner-only actions, and balance conservation.
== Labels, Deduplication, and Splits
- Each record is a tuple (contract, property, label, provenance).
- We deduplicate by bytecode hash and by near-duplicate detection.
- Splits are made by contract family to prevent leakage, then frozen and hashed.
- Targets: at least 2k labelled pairs, at least 30% of them mutants and at least 10% real exploits.
- We provide a datasheet with sizes, class balance, and provenance, and `make data` rebuilds the dataset.
== Threats to Validity
- Mutant-artifact leakage: we report metrics on a real-only test set and on unseen mutation operators.
- Few real bugs: we report real-only and mutant results separately.

= Methodology <sec-method>
// Outline from PLAN.md Stages 2-6, mapped to RQ1-RQ4.
#todo[Expand as each stage lands.]
== Research Questions
- *RQ1 (mechanism):* are scoring-rule screeners and certificate-paid provers jointly incentive compatible under delayed, one-sided ground truth?
- *RQ2 (routing):* does ML routing raise recall\@budget over uniform and heuristic routing, and does it stay robust to deflating, lazy, or colluding screeners?
- *RQ3 (certificates):* which certificate types are cheap enough to check that they can be slashable?
- *RQ4 (ML):* how calibrated can a bytecode screener be, and how does calibration translate into market efficiency?
== FV Pipeline and Certificate Costs (RQ3)
- Halmos and hevm runners with uniform JSON output: verdict, depth $k$, timeout, path count, time, and memory.
- Counterexamples are converted into Foundry tests and replayable traces, and we record their replay gas.
- Bounded-safe claims are tagged with (tool, $k$, timeout).
- Unbounded claims use CHC invariants (SMTChecker, Eldarica, or Z3 Spacer), re-checked with one query per clause.
- Measurements: solve versus check cost for each certificate type, and the empirical $rho_"bnd"(k) = P("bug" | "bounded-safe at depth" k)$ estimated from mutants, for at least three depths.
== ML Screeners (RQ4)
- *Baselines:* opcode n-grams with logistic regression or gradient boosting, and Slither/Mythril feature heuristics.
- *Stronger models:* a GNN on CFG basic blocks, and/or a small opcode transformer.
- *Calibration:* temperature or isotonic scaling. We report ECE, Brier score, log-loss, AUROC, and recall\@budget, over 5 seeds with confidence intervals.
- *Shift tests:* a real-only test set and unseen mutation operators.
== Mechanism Analysis and Simulation (RQ1, RQ2)
- Formal statements:
  - incentive compatibility of screener reporting under an IPW audit;
  - a bond bound $b > P / (1 - phi)$;
  - manipulation bounds under the $eta$ floor and stake caps.
- An agent-based simulation with parameters calibrated from the measured certificate costs, $rho_"bnd"$, and screener calibration. It sweeps the fraction of deflating, lazy, Sybil, and colluding agents.
== On-Chain Prototype
- Foundry implementations of `ScreenerBook`, `ProverRegistry`, `Router`, and `Escrow`.
- Unit, fuzz, and invariant tests: bond conservation, no double payout, and monotonic refutation windows.
- Gas is measured for each report and claim.
== Experiments
- E1: routing recall.
- E2: coalition robustness.
- E3: settlement cost and latency per certificate type.
- E4: economics (payouts, bond sizes, break-even TVL, gas).
- E5: ablations (no $eta$ floor, median instead of robust aggregator, no IPW).

= Evaluation
#todo[FV pipeline (Halmos/hevm, SmartBugs Curated, mutation), screener baseline, agent-based simulation, Foundry escrow demo.]

= Discussion <sec-discussion>
#todo[Limitations: checking-cost asymmetry, Alethe array gap; zkVM circuits as future target.]

= Conclusion
#todo[]

#bibliography("/related-work/references.bib", style: "ieee")
