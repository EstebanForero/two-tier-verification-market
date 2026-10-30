# PLAN — Two-Tier Verification Market for EVM Bytecode

Owner: Esteban Forero · Coordinator: Lead Researcher · Created 2026-10-30
Target: ~24 weeks (6 months) to arXiv preprint; one student + agent team; laptop + modest GPU.
Repo: https://github.com/EstebanForero/two-tier-verification-market (monorepo)

## Research questions
- RQ1 (mechanism): Can proper-scoring-rule screeners + certificate-paid provers be jointly incentive-compatible when ground truth is delayed and one-sided?
- RQ2 (routing): Does ML routing of a fixed FV budget raise bug recall vs uniform/heuristic routing, and stay robust to coalitions of deflating/lazy screeners?
- RQ3 (certificates): Which EVM certificate types (counterexample traces, bounded-safe, CHC invariants) are cheap enough to check to be slashable?
- RQ4 (ML): How well-calibrated can a bytecode/CFG screener be on real + mutant bugs, and how does calibration translate into market efficiency?

## Stage overview
| # | Stage | Owner | Weeks | Depends on |
|---|-------|-------|-------|------------|
| 0 | Infra: repo, CI, conventions | Lead Researcher | 0–1 | – |
| 1 | Dataset v1 (SmartBugs Curated + mutants + labels) | Verification Researcher | 1–4 | 0 |
| 2 | FV pipeline + certificate checking + cost measurement | Verification Researcher | 2–7 | 1 (partial) |
| 3 | ML screeners: baselines → GNN/transformer, calibration | Verification Researcher (ML) + Lead | 4–11 | 1 |
| 4 | Mechanism theory + simulation v0.2 → v1.0 | Mechanism Designer | 1–12 | 2,3 for calibrated params |
| 5 | Solidity contracts (ScreenerBook, ProverRegistry, Router, Escrow) + Foundry tests | Protocol Researcher | 6–14 | 4 (v0.3 rules) |
| 6 | End-to-end experiments | Lead + all | 12–18 | 2,3,4,5 |
| 7 | Paper (Typst) → arXiv | Paper Writer (Typst) | continuous; final 18–24 | all |
| X | Novelty watch / related work full reads | Ideation Agent + Protocol Researcher | continuous | – |

## Stage 0 — Infrastructure (wk 0–1) · Lead Researcher
- Goal: one public monorepo with CI that compiles the paper and runs tests.
- Deliverables: repo skeleton (`contracts/ ml/ fv/ sim/ paper/ data/ experiments/`), README roadmap, MIT license, GitHub Actions CI.
- Exit: CI green on `main`; every agent can push via PRs/branches.

## Stage 1 — Dataset v1 (wk 1–4) · Verification Researcher
- Goal: labelled corpus of (contract, property, label, provenance).
- Deliverables:
  - `data/smartbugs/`: SmartBugs Curated (≈143 contracts, DASP categories) pinned by commit, compiled with solc-select to runtime bytecode + CFG (evmole/ethir or solc --asm).
  - `data/mutants/`: mutation injection (SuMo / Gambit-style operators: reentrancy, unchecked call, access-control removal, arithmetic, tx.origin) with seeds; record operator, location, and whether a Halmos property kills it.
  - `data/real/`: real exploit/audit labels — DeFiHackLabs reproductions, SolidiFI, Web3Bugs/Code4rena findings (license-checked), plus "presumed safe" set (audited, long-lived, high-TVL contracts) with explicit one-sided-label caveat.
  - Property templates per contract (no-drain, withdraw-always-possible, owner-only, balance-conservation) as Halmos `check_` functions.
  - Datasheet: sizes, class balance, dedup (bytecode hash + near-duplicate), train/val/test split *by contract family* to avoid leakage.
- Exit: ≥2k labelled (contract,property) pairs; ≥30% mutant, ≥10% real-exploit; split frozen with hash; `make data` reproducible.
- Risks: mutant leakage (ML learns mutation artefacts) → measure with "real-only" test set; solc version zoo → pin per-contract.

## Stage 2 — FV pipeline & certificates (wk 2–7) · Verification Researcher
- Goal: measured cost model for each certificate type.
- Deliverables:
  - `fv/` runners for Halmos and hevm (symbolic) with uniform JSON output (verdict, depth k, timeout, paths, wall time, memory).
  - Counterexample replay: convert model → Foundry test → on-chain-replayable trace; check cost (gas) recorded.
  - Bounded-safe claims tagged (tool, k, timeout); unbounded attempts via CHC (solc SMTChecker CHC engine / Eldarica/Z3 Spacer) with invariant re-check (one SMT query per clause).
  - Cost table: solve time vs check time per certificate type; empirical ρ_bnd(k) = P(bug | bounded-safe at depth k) using mutants with known ground truth.
- Exit: cost table over full dataset; ρ_bnd curve for ≥3 depths; decision on whether UCERT is practical (answers open question 4).
- Risks: solver blow-up → timeouts are data, not failures; Alethe lacks arrays → rely on CHC invariants + replayable CEX.

## Stage 3 — ML screeners (wk 4–11) · Verification Researcher (ML) with Lead
- Goal: calibrated P(bug | contract, property).
- Steps: (a) baselines: opcode n-gram + logistic regression / gradient boosting, Slither/Mythril-feature heuristics; (b) stronger model: GNN (GATv2/GIN via PyTorch Geometric) on CFG basic blocks, and/or small transformer on opcode sequences (fine-tune a code model e.g. CodeBERT-size or a ~20–50M param model from scratch); (c) calibration: temperature/isotonic scaling, report ECE, Brier, log-loss, AUROC, recall@budget; (d) adversarial/shift tests: real-only test set, unseen mutation operators.
- Compute options: laptop CPU for baselines (minutes); laptop GPU or Colab/Kaggle free T4 for GNN (hours); rented single A10/A100 (~$1–2/h, budget ≈ $50–150) only for transformer pretraining on unlabelled verified bytecode (e.g. Etherscan/Sourcify dump).
- Deliverables: `ml/` package, training configs, model cards, checkpoints (GitHub Releases / HF Hub), calibration plots.
- Exit: best model beats baselines on recall@15%-budget on the real-only test set, ECE ≤ 0.05 after calibration; seeds ×5 with CIs.
- Risks: tiny real-bug set → heavy reliance on mutants; report both.

## Stage 4 — Mechanism theory & simulation (wk 1–12) · Mechanism Designer
- v0.2 (wk 1–3): prover tier, refutation window, leave-one-out reference, ≥20 seeds with CIs.
- v0.3 (wk 3–6): robust aggregator (stake-capped trimmed log-odds vs reputation-weighted), η sizing, Sybil-resistant geometric mutant-kill split, CEX-withholding vs TVL-indexed bounty.
- v1.0 (wk 7–12): parameters calibrated from Stage 2 costs/ρ_bnd and Stage 3 model calibration; formal statements + proofs (IC for screeners under IPW audit; bond bound b > P/(1−φ); manipulation bounds under η floor + caps).
- Deliverables: `sim/` package (numpy, pytest), `sim/theory/` notes, figure scripts.
- Exit: theorems written; sim reproduces with one command; attack sweeps (deflator/lazy/Sybil/collusion fraction) plotted.

## Stage 5 — Solidity contracts (wk 6–14) · Protocol Researcher
- Contracts: `ScreenerBook` (commit-reveal reports, stake), `ProverRegistry` (bonds, claim tags), `Router` (η-floor routing from snapshotted q̂, randomness beacon), `Escrow` (bounties, refutation window, slashing, split φ), oracle/committee adapter (explicit trust assumption).
- Testing: Foundry unit tests, fuzz tests, invariant tests (bond conservation, no double payout, window monotonicity), gas reports; Halmos on our own contracts (dogfooding).
- Exit: ≥90% line coverage, invariants pass 10k runs, gas per report/claim measured; deploy script to a local anvil + Sepolia (optional, user-approved).

## Stage 6 — End-to-end experiments (wk 12–18) · Lead + all
- E1 Routing: recall@budget for uniform vs heuristic vs ML routing on the real dataset with real FV costs.
- E2 Robustness: coalition attacks on aggregator (sim + anvil replay).
- E3 Certificates: settlement latency and cost per certificate type.
- E4 Economics: payouts, bond sizes, break-even TVL; gas on-chain.
- E5 Ablations: no η floor, median vs robust aggregator, no IPW.
- Exit: all figures generated by `experiments/` scripts from pinned artefacts; results table frozen.

## Stage 7 — Paper (continuous; final wk 18–24) · Paper Writer (Typst)
- Sections already skeletoned; fill per stage. Cite only sources read in full (Protocol Researcher full-read list).
- Deliverables: Typst PDF via CI; arXiv version (Typst PDF upload is accepted by arXiv as PDF-only, or port to LaTeX if venue needs it); artefact appendix linking repo tag + Zenodo DOI.
- Target venues: AFT, FC, or IEEE S&B / workshop first; arXiv on completion.
- Exit: internal review pass by all agents; user approval before any submission (external action).

## Testing strategy & CI (GitHub Actions)
- `paper` job: install Typst, `typst compile --root . paper/main.typ`, upload PDF artifact.
- `python` job: pytest for `sim/` (and later `ml/`, `fv/` unit tests with tiny fixtures; no solver/GPU in CI).
- `contracts` job (Stage 5): `forge build`, `forge test`, `forge coverage` (added when contracts land).
- Nightly/manual job (later): small Halmos run on 5 contracts to catch pipeline regressions.
- Rules: branch per stage, PRs into `main`, CI must be green; fixed seeds; data/artefacts versioned by hash, large files outside git (Releases/HF).

## Compute needs
- CPU laptop: dataset, baselines, sim, Foundry, Halmos (hours per full sweep; parallelise per contract).
- GPU: free Colab/Kaggle T4 sufficient for GNN; optional rented A10/A100 ≈ $50–150 total for transformer pretraining.
- Storage: <20 GB (bytecode corpus + solver logs); proofs can be large (Carcara 92 GB precedent) → store summaries only.

## Key risks
| Risk | Mitigation |
|---|---|
| Overlap from new prior work | Ideation Agent weekly novelty watch; pivot contribution framing |
| Too few real bug labels | Mutants + DeFiHackLabs; report real-only metrics separately |
| UCERT impractical for EVM | Make CEX-first + bounded claims the main path (already designed) |
| Mutant artefact leakage | Indistinguishability tests; unseen-operator test split |
| Sim ≠ reality | Calibrate sim from Stage 2/3 measurements |
| Scope creep (long project) | Stage exit criteria gate the next stage |
| Citation hygiene | Only full-read sources cited in final paper |
