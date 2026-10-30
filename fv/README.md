# fv — Halmos kill pipeline (Stage 1 prototype; owner: Verification Researcher)

Tools (box, 2026-10-30): halmos 0.3.3 (pip, venv), forge 1.8.7 (foundryup stable), solc 0.8.24 for harnesses,
forge-std **pinned v1.9.4** (vendored in `halmos/lib/forge-std`). hevm: **not installed / not run**.

## Layout
- `halmos/src/Targets.sol` — single-transaction 0.8 ports of SmartBugs Curated contracts: `V` = original bug
  (wrapped in `unchecked` to keep 0.4 wrap-around semantics), `F` = manual fix, `M_*` = mutant of F (operator in name).
- `halmos/src/Seq.sol` — stateful targets with uniform `op(a,x)` / `inv()` interface for depth-bounded checks.
- `halmos/test/Props.t.sol` — property templates as `check_` functions: no-wrap (`count` monotone), no-inflation
  (transfer), solvency (`paidOut <= paidIn`), no-drain (reentrancy attacker cannot extract > deposit), checked-call
  (failed callee ⇒ caller reverts).
- `halmos/test/Seq.t.sol` — `check_seq_k{1,2,3,4,6,8}`: k = number of transactions (compile-time bound; halmos
  `--loop` does NOT bound a constant-trip loop, see below).
- `run_rho.py` — depth sweep + forge replay of every counterexample → `results/rho_bnd_runs.csv`.

## Reproduce
```
python3 -m venv .venv && . .venv/bin/activate && pip install halmos==0.3.3
curl -L https://foundry.paradigm.xyz | bash && foundryup
cd fv/halmos && forge clean && halmos            # property templates (exit code 1 is EXPECTED, see below)
cd .. && python run_rho.py results/rho_bnd_runs.csv 60
```

## Halmos "exit code 1" — diagnosis and fix
There was no failing run committed in the repo; the exit-1 run is the prototype run in
`/workspace/research/two-tier-market/verification/pipeline/` (`results_halmos.json` → `"exitcode": 1`). Three
distinct causes, in the order they appeared:
1. **`Unsupported cheat code: deployCode(string)` → every test ERROR.** forge ≥1.x defaults to
   `dynamic_test_linking = true`, which compiles `new C()` inside tests into `vm.deployCode(...)` helper calls
   (`VmContractHelper*` artifacts); halmos 0.3.3 does not implement that cheatcode.
   Fix: `dynamic_test_linking = false` in `foundry.toml` + pin forge-std v1.9.4 (latest forge-std also triggered it).
2. **`Skipped *.json due to parsing failure: KeyError: 'ast'` → "No tests".** Stale `out/` built by a plain
   `forge build` (no AST). Fix: `forge clean` before halmos (halmos builds with `--ast`).
3. **Remaining exit 1 = by design.** halmos exits 1 if *any* `check_` fails or times out. In a kill pipeline the
   buggy variants (V, M) are *supposed* to produce counterexamples, and `check_MulF` hit the 60 s assertion-solver
   TIMEOUT (256-bit nonlinear `count*i/i==count`). Fix: never use the process exit code as the verdict; parse
   `--json-output` per test (`exitcode` 0 = safe-within-bounds, 1+models = cex, TIMEOUT/ERROR) and compare to the
   expected label (`run_rho.py` does this).
Also found: v1 transfer property (`a+b == x+y`) was **too weak** — it holds modulo 2^256, so all three transfer
variants "passed" including the buggy ones. Replaced with no-inflation; this is a concrete example of why a
bounded/`safe` claim must name the property hash (spec bugs pass silently).

## Prototype single-tx results (real run, 2026-10-30, 60 s solver timeout; before the transfer-spec fix)
| test | verdict | time | cex |
|---|---|---|---|
| AddV / AddM_unchecked | FAIL (cex) | 0.13 / 0.12 s | i = 2^256-1 |
| AddF | PASS | 0.02 s | – |
| SubV / SubM_relop | FAIL | 0.12 / 0.12 s | i = 2^255 / i = 2 |
| SubF | PASS | 0.14 s | – |
| MulV | FAIL | 0.55 s | i = 2^255 |
| MulF | **TIMEOUT** | 60.14 s | – |
| WalletV (2-call) | FAIL | 0.06 s | v = 2^254, k = 0 |
| WalletF | PASS | 0.05 s | – |
| BankV (reentrancy, concrete attacker) | FAIL | 0.14 s | d = 1, o = 2^99 |
| BankF | PASS | 0.14 s | – |
| RetV / RetF | FAIL / PASS | 0.12 / 0.01 s | – |
| XferV / XferF / XferM_delreq | PASS ×3 (weak spec) | 0.06–0.48 s | – |
Wall clock for the whole run: 67.7 s.

**Re-run after the spec fix (props_v2, 2026-10-30, `results/props_v2.log`):** same verdicts for Add/Sub/Mul/Wallet/Bank/Ret
(MulF TIMEOUT 60.11 s again). Transfer with the no-inflation property: XferM_delreq **FAIL (killed)**, XferF PASS, XferV PASS.
XferV still passes because the harness assumes `x + y` does not overflow (bounded total supply), and under that
assumption its unchecked `+=` cannot wrap. This is a correct "safe" under a stated assumption, so the claim scope has to include the assumptions.

## Kill status of the 2,093 dataset mutants
See `kill/` (differential kill, below). The text that follows was the earlier plan.
Earlier status: NOT done. Properties above are hand-written per ported contract; the 2,093 mutants are 0.4.x sources compiled
with old solc and have no generic harness yet. `pairs.csv` therefore has no `fv_killed` column; "keep only killed
mutants" (novelty-watch #6) is **pending**. Plan: bytecode-level generic properties (no-selfdestruct-by-stranger,
no-ETH-drain-by-stranger, owner-slot-unchanged-by-stranger) run on deployed runtime bytecode via `vm.etch`.

## kill/ — differential Halmos kill filter over all dataset mutants
`kill/kill.py` etches the original and the mutant runtime bytecode at two addresses, makes the same symbolic call
on both (selector + 2 symbolic words, symbolic sender, symbolic value < 2^96), and asserts equal success flag, returndata,
ETH balance and storage slots 0–7. A mutant counts as **killed** if Halmos finds a counterexample, **equiv_bounded** if no
difference exists in this scope, and **timeout** if there is no model within the 10 s solver timeout (or another failure).
Limits: one call, starting from empty storage (no constructor state), and only 2 argument words. This is
non-equivalence, i.e. a kill against a differential property, not against a security property. `results/kill.csv`.

Results: killed 755 / equiv_bounded 352 / timeout 402 / error (wall cap) 584 of 2,093; see data/DATASHEET.md.
