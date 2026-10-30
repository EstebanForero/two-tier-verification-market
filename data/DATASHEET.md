# Datasheet — SmartBugs-Curated mutant pairs v0 (stage1/dataset)

**Built:** 2026-10-30 by `data/scripts/build_dataset.py --seed 1337 --order2 20` (seed and order recorded in `summary.json`).
**Source:** SmartBugs Curated, pinned in `data/smartbugs.lock` (commit `230e649123477eff332742a59a1c7cc6dc286cab`,
2024-06-16). Fetch with `data/scripts/fetch_smartbugs.sh`. Generated artifacts (`data/build/`) are gitignored and
rebuild deterministically (~1 min on the box).

## Composition (measured)
- 143 originals (families) compiled to runtime bytecode with the per-file solc in SmartBugs `versions.csv`
  (0.4.0–0.5.0, all 143 compile) → `data/build/orig/*.bin-runtime` + `*.cfg.json` (basic blocks + static jump edges,
  `data/scripts/evmcfg.py`; dynamic jumps not resolved; CBOR/bzzr metadata stripped).
- **2,093 labelled (original, mutant) pairs**: 1,053 first-order mutants (one per mutation site) + 1,040 seeded
  second-order mutants (≤20 random site pairs per family). 2,135 mutants generated; dropped 39 that failed to
  compile, 1 identical to original bytecode (equivalent mutant), 2 duplicate runtimes.
- Operators (first order): DELREQ 389, RELOP 311, TXORIGIN 126, UNCHK 104, DELMOD 54, DELTHROW 38, SAFEMATH 19, REENT 12.
  Operator → class: DELREQ/DELTHROW/TXORIGIN/DELMOD → access_control; UNCHK → unchecked_low_level_calls;
  RELOP/SAFEMATH → arithmetic; REENT → reentrancy (state reset moved after the external call).

## Frozen split (by family)
`split = sha256(family path) mod 100`: <70 train, <85 val, else test. It is independent of the seed and of dataset
size, so all mutants of one original stay in the original's split and the assignment never changes.
| split | families | mutant pairs |
|---|---|---|
| train | 103 | 1,538 |
| val | 25 | 269 |
| test | 15 | 286 |

## Columns (`pairs.csv`)
family, variant (`orig` / `m1_NNN` / `m2_NNN_MMM`), split, solc, main (contract under test = largest runtime;
heuristic), runtime_sha256, operators, injected_class, sb_labels (SmartBugs category labels of the original),
lines (1-based mutated lines), is_mutant.

## Label semantics and caveats (read before use)
- Every SmartBugs original is *already vulnerable*. A mutant's label is `sb_labels ∪ injected_class`. There are no
  verified-clean contracts in this set; class-negatives are just "no label of this class".
- **Injected ≠ semantically buggy.** Mutants are syntactic. Not all are exploitable (e.g. RELOP on a non-security
  comparison, DELREQ on an input sanity check). `fv_killed` (Halmos property violated by mutant but not original)
  is **not yet computed** for the 2,093 mutants; only hand-ported prototypes were killed (see `fv/README.md`).
- Mutant-vs-real distinguishability: measured gate AUC on the family-split test set is 0.827 (original vs own
  mutants) — mutants are fingerprintable. See `ml/README.md`.
- All-0.4/0.5 bytecode. A detector can learn the compiler version. Match solc whenever mixing with other sets.
- No exploit or audit labels in this branch (owned by `stage1/labels`).

## DAppSCAN-Bytecode (real-bug set; NOT in repo)
No license, so it is processed outside the repo: `data/dappscan/fetch_dappscan.sh` → `/workspace/data/dappscan/repo`
(commit 66a56619), `data/dappscan/process_dappscan.py` → `/workspace/data/dappscan/derived/`. Measured:
888 SWC labels → 539 in SWC {101,104,105,107,112,113,114,115,128} → 237 unique contracts (19 empty runtimes
dropped, 0 hash duplicates among kept) from 76 DApps; DApp-hash split train/val/test = 158/18/61 contracts; 138
compiled with solc ≥0.6. Label→function→PC mapping via AST `FunctionDefinition.src` + `srcmap-runtime`: 187/539
labels mapped (the rest have function `N/A` or names not found in the AST). Labels are positive-only.
