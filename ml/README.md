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
- **`gate.py` (run 2026-10-30, `results/gate_metrics.json`, gitignored).** Eval = val+test splits. Each gate is
  also run with a length-only baseline (log of bytecode length) as a confound control.

| gate | AUC opcode model | AUC length-only | eval mutants / others |
|---|---|---|---|
| A mutant vs own SmartBugs original | 0.783 | 0.656 | 555 / 40 |
| B mutant vs DAppSCAN (solc<0.6) | 1.000 | 0.781 | 555 / 26 |
| B2 same, exact solc match (0.4.0–0.5.0 intersection) | 1.000 | 0.862 | 242 / 7 |
| C mutant vs SolidiFI (all, solc 0.5.0/0.5.12) | 1.000 | 0.939 | 555 / 91 |
| C2 SolidiFI exact solc | skipped: only 1 mutant compiled with 0.5.0 | | |
  Reading: mutants are perfectly separable from other corpora even with solc matched. Bytecode size alone gives
  AUC 0.78–0.94, so the gate mostly detects the corpus (SmartBugs toy contracts vs production code), not
  mutation artifacts. The only like-for-like gate (A, same code base) gives 0.78. Eval negatives are tiny (7–91).
- SolidiFI: commit 4b0573e, 350/350 compiled, 350 unique runtimes, kept in /workspace/data/solidifi (contracts
  keep their Etherscan licenses, so no data goes in the repo). Its bugs are injected too, so it is not a real-bug set.
- DeFiHackLabs: **not fetched / not run** (victim bytecode needs chain RPC or explorer access, not set up).

## Length-matched gate (round 3, `ml/gate_matched.py`)
Mutants matched to each "other" contract by nearest log bytecode length (caliper 0.10, 2 mutants per other, no replacement);
grouped 5-fold CV (group = SmartBugs family / DApp / SolidiFI base contract); out-of-fold AUC, 95% CI by 1000x group bootstrap.

| gate | n mut / other (groups) | length-only | opcode LR | opcode + length |
|---|---|---|---|---|
| mutant vs DAppSCAN solc<0.6 | 117 / 59 (33 / 24) | 0.344 [0.209, 0.498] | 0.971 [0.918, 0.996] | 0.966 [0.903, 0.994] |
| mutant vs DAppSCAN all | 298 / 151 (38 / 62) | 0.478 [0.321, 0.621] | 0.984 [0.964, 0.998] | 0.985 [0.966, 0.999] |
| mutant vs SolidiFI | 438 / 222 (17 / 50) | 0.360 [0.178, 0.548] | 0.996 [0.986, 1.000] | 0.995 [0.983, 1.000] |
| mutant vs own original | 208 / 115 (115 families) | 0.519 [0.507, 0.531] | 0.737 [0.693, 0.781] | 0.707 [0.670, 0.748] |

**Verdict:** matching removes length as a signal (length-only AUC at or below chance), yet the opcode gate *still separates*
mutants from DAppSCAN and SolidiFI almost perfectly. So the corpus-level separation is not a length artifact; it is a
corpus/provenance artifact (SmartBugs source style, compiler versions, contract idioms), i.e. the gate learns "which corpus",
not "is buggy". Adding length as a covariate adds nothing. Only the within-family gate (mutant vs its own original, 0.74)
measures bug-relevant signal, and it is modest. Cross-corpus AUCs must not be reported as bug detection.
