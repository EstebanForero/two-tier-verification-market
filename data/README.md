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
| presumed_safe.csv | 7 | Ethereum mainnet: UniswapV3Factory, SwapRouter, NonfungiblePositionManager, Permit2, WETH9, Safe 1.3.0 singleton, Safe 1.3.0 ProxyFactory |
| Code4rena | 0 | excluded on license/ToS grounds (see SOURCES.md) |

## Presumed-safe criteria
Contract must be (1) on Ethereum mainnet ≥ ~3 years, (2) widely used (core infrastructure of Uniswap/Safe/WETH), (3) publicly audited / open source, (4) address taken from the project's own deployment source at build time, (5) **not** listed as a vulnerable contract in DeFiHackLabs (automatic filter). This label means "no known exploit of the contract's own logic", **not** verified safe. Permit2/routers have been involved in phishing/approval-abuse losses, which are not contract bugs.

## Known biases / limitations
- DeFiHackLabs: survivorship of reproducible, mostly-DeFi incidents; heavily BSC/Ethereum; 575 rows lack an address (non-standard PoC headers); `vuln_category` is free text (no taxonomy) and only set for 164 rows; README coverage of older years partial; PoCs labelled by attack, so one contract can appear multiple times; "exploited" ≠ the only bug.
- SolidiFI: synthetic injected bugs in old (Solidity 0.4/0.5) Etherscan contracts — distribution unlike real bugs; many bugs per file.
- Presumed-safe: tiny (7), hand-picked, high-profile — strong selection bias; not a negative class to train on at scale.
- No audit-finding labels yet (Code4rena excluded). Possible permissive alternatives to check next: SmartBugs-curated, DAppSCAN, Solodit (check terms).
