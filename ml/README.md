# ml — calibrated screener baseline + mutant/real gate (Stage 1)

`baseline.py` reads `data/build/ds/pairs.csv` + `bin/` and, if present, `/workspace/data/dappscan/derived/`
(outside the repo, no license). Output: `results/baseline_metrics.json` (all numbers below come from that file, run 2026-10-30).

**Model:** opcode 1–3-gram TF-IDF over runtime bytecode (PUSH immediates dropped, metadata stripped) → one-vs-rest
logistic regression (C=1, class-balanced) per class → isotonic calibration fit on **val** families. Split =
frozen family split (train 1641 / val 294 / test 301 contracts incl. originals). FNR@FPR uses a threshold at the
5% / 0.5% quantile of test negatives. With ≤ 200 negatives, FPR 0.5% is effectively "zero FP", so read it as that.

## Screener (test families, n=301; mutant-only and real reported separately)
| class | AUC all | AUC mutant-only | ECE all | FNR@FPR5% | real DAppSCAN AUC (n=237) | real ECE |
|---|---|---|---|---|---|---|
| access_control | 0.804 | 0.796 | 0.157 | 0.476 | 0.318 | 0.667 |
| arithmetic | 0.861 | 0.869 | 0.023 | 0.988 | 0.526 | 0.255 |
| reentrancy (9 pos) | 0.709 | 0.675 | 0.025 | 0.556 | 0.472 | 0.326 |
| unchecked_calls | 0.921 | see json | 0.202 | 0.101 | see json | see json |
Main result: **the screener does not transfer.** On real DAppSCAN bugs, AUC is at chance or worse and ECE is 0.25–0.67.
Mutant-trained calibration says nothing about real-bug calibration, so report the two separately. "Negatives" in
DAppSCAN are contracts labelled only with *other* SWCs (labels are positive-only), so they are noisy negatives.
On SmartBugs orig-only (n=15), calibration is meaningless (1–2 positives per class).

## Gate (is this bytecode a mutant or a real program?)
- **A: SmartBugs original vs mutants** (test families): AUC 0.827, FNR@FPR5% 0.696; only 15 originals in test.
- **B: mutants vs DAppSCAN real-bug contracts, solc < 0.6 only**: AUC **1.000** (73 real in train, 26 real in eval
  from DAppSCAN val+test DApps). Not a meaningful success: the two sets differ in codebase size/style and partly in
  compiler (DAppSCAN includes 0.5.10–0.5.17, mutants ≤0.5.0). The gate is detecting the corpus, not the
  "mutant-ness". Next step: an exact solc-version match plus size-matched sampling, or a within-contract gate.
- DeFiHackLabs / SolidiFI labels: **not fetched, not run.**
