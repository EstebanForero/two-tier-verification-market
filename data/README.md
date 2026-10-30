# data — Stage 1 labels (branch stage1/labels)

Regenerate: `scripts/build_all.sh` (clones sources into `$SRC_DIR`, default /tmp/ttvm-src; needs git + python3, no deps). `scripts/merge.py` also writes a combined `data/labels.csv` (not committed; it's a concatenation).
Licenses/URLs: see `SOURCES.md`. Every row has a `reference_url` pinned to the exact upstream commit or page it came from. No rows were hand-written.

## Schema (all CSVs)
`id, source, chain, address, file_path, contract_name, label, vuln_category, date, reference_url, license, source_commit`
- `label` ∈ {`exploited`, `injected_bug`, `presumed_safe`}
- `address`: lower-case, only when the source states it; `chain` is derived from the explorer domain.
- `file_path`: upstream path (SolidiFI: `buggy_contracts/<cat>/buggy_N.sol#L<loc>+<length>`).

## Counts (build of 2026-10-30)
| file | rows | notes |
|---|---|---|
| defihacklabs_exploits.csv | 920 | one per PoC file; 345 have a parsed vulnerable address+chain; 164 matched to a README heading (exact date + free-text description in `vuln_category`); the rest have month-only date (`YYYY-MM` from folder) and empty category |
| solidifi_injected.csv | 9,369 | one per injected bug, 7 categories × ~50 contracts: Timestamp-Dependency 1381, Unhandled-Exceptions 1374, Re-entrancy 1343, TOD 1336, tx.origin 1336, Overflow-Underflow 1333, Unchecked-Send 1266 |
| presumed_safe.csv | 25 | Ethereum mainnet; 58 candidates from official deployment sources, 25 pass all filters (per-candidate evidence in `presumed_safe_evidence.csv`): Uniswap v2 (2), Uniswap v3 (12 incl. Permit2, staker, multicalls), WETH9, Safe (7), Aave v3 (3) |
| solodit_audit_findings.csv | 0 | script ready (`scripts/build_solodit.py`), needs `SOLODIT_API_KEY` |
| Code4rena | 0 | excluded on license/ToS grounds (see SOURCES.md) |

## Presumed-safe criteria (scripts/build_presumed_safe.py)
Candidates: only addresses parsed at build time from official sources — Uniswap v2/v3 deployment docs, safe-global/safe-deployments v1.3.0+v1.4.1 (mainnet entries), bgd-labs/aave-address-book `AaveV3Ethereum.sol` (selected core constants). Each row's `reference_url` is that source; `source_commit` holds the creation tx.
All must hold (checked automatically, evidence in `presumed_safe_evidence.csv`):
- C1 age: creation tx (Blockscout) ≥ 2 years before 2026-10-30.
- C2 source code verified on Blockscout.
- C3 usage: ≥ 50 transactions (one full Blockscout transactions page). Blockscout's `/counters` endpoint undercounts badly (e.g. 3 for Uniswap SwapRouter), so it's recorded but not used. This is a *liveness* floor, not a TVL measure — TVL was not checked.
- C4 address not a vulnerable contract in `defihacklabs_exploits.csv`.
- C5 project-level: Uniswap, Safe, Aave v3 and WETH9 have public audit reports (project-level fact, not checked per contract).
Excluded by filters: young contracts (UniversalRouter 1.76y, Aave WETH_GATEWAY 1.71y, Safe migration libs) and low-use helpers/eip155 duplicates.
Not checked against incident lists beyond DeFiHackLabs (e.g. rekt.news, SlowMist) — TODO. This label means "no known exploit of the contract's own logic", **not** verified safe. Permit2/routers have been involved in phishing/approval-abuse losses, which are not contract bugs.

## Known biases / limitations
- DeFiHackLabs: survivorship of reproducible, mostly-DeFi incidents; heavily BSC/Ethereum; 575 rows lack an address (non-standard PoC headers); `vuln_category` is free text (no taxonomy) and only set for 164 rows; README coverage of older years partial; PoCs labelled by attack, so one contract can appear multiple times; "exploited" ≠ the only bug.
- SolidiFI: synthetic injected bugs in old (Solidity 0.4/0.5) Etherscan contracts — distribution unlike real bugs; many bugs per file.
- Presumed-safe: 25 contracts from 4 blue-chip projects — strong selection bias (well-funded, heavily audited, mostly infra/router code); C3 is a weak usage proxy; proxies are labelled at the proxy address (implementation may change, e.g. Aave POOL).
- No audit-finding labels yet (Code4rena excluded). Round 2: DAppSCAN excluded (no license), SmartBugs-wild has no audit labels, Solodit permitted for derived metadata but needs an API key (see SOURCES.md).
