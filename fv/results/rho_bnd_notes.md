# rho_bnd: P(bounded check reports "safe" | contract is buggy) — first measurements (2026-10-30)

**File:** `rho_bnd_runs.csv` (same columns as requested, plus target, gt_source, bug_min_depth, replay_time_s).

## Method
- Tool: halmos 0.3.3 + forge 1.8.7 on one shared box (no isolation; times are wall clock and include roughly 1.2 s of compile
  and start-up per call). Harness: `fv/halmos/test/Seq.t.sol`. `check_seq_k<k>(ops, xs[12])` runs k symbolic
  transactions (the operation selector and argument are both symbolic, the sender is symbolic) and then asserts the target's `inv()`.
  k ∈ {1,2,3,4,6,8}; `--loop 16`; assertion-solver timeout 60 s (SWalletV/F, SMultiV k≤6) then 30 s for
  the rest, after the run was restarted to fit the time budget (the `timeout_s` column records which). Hard wall cap per call:
  4×TO+60 s, later 3×TO. After a timeout or error, deeper k for the same target is skipped (not recorded).
- Every cex is replayed concretely with `forge test` on a generated contract; `cex_replayed=True` means the violation reproduced.
- Targets (ground truth by construction): SWallet (0.8 port of the SmartBugs wallet refund bug, min depth 3),
  SMulti (multi-tx overflow, depth 2), Gate* (synthetic access-control gate needing d unlock steps, d = 3, 6, 10), plus
  the fixed versions (F).
- **Sample size: 8 targets, 5 buggy. This is a feasibility probe, not an estimate of rho for SmartBugs.** The 2,093
  dataset mutants were not run (no generic harness yet).

## Results (measured)
- No false cex: none of the 3 fixed targets ever produced a cex. Every cex (12/12) replayed.
- Buggy target with k < min bug depth ⇒ "safe" (by construction a bounded miss): SWalletV k1–2, SMultiV k1, GateM3 k1–2,
  GateM6 k1–3, GateM10 k1–6 (k8 timeout). These rows are the rho_bnd events.
- Cost explodes with k: SWalletV cex at k3 1.7 s → k4 4.1 s → k6 74 s → k8 timeout (300 s). GateM6 timed out at k4 (138 s)
  before reaching its bug depth 6, so a *timeout*, not a safe, is what a depth-6 bug produced here.
- Fixed targets: safe up to k6 (2–25 s; SWalletF k6 "error" after 195 s, i.e. solver failures without a model) and timeout at k8.
- Take-away for the mechanism: in this harness, rho_bnd(k) ≈ 1 for bugs deeper than the largest k that completes within
  the timeout (here ≈ 6 tx at 30–60 s), and ≈ 0 for shallower bugs. The useful parameter is the depth distribution
  of real bugs, which we have **not measured**.

## Published numbers
None cited. I have not read a published measurement of bounded-model-checking miss rate versus depth for EVM
contracts during this task, so no number is quoted. Related sources read earlier (no rho numbers taken from them):
hevm limitations https://hevm.dev/limitations-and-workarounds.html; SmartBugs ICSE'20
https://www.inesc-id.pt/wp-content/uploads/2024/04/ICSE2020_Ferreira-1.pdf.
