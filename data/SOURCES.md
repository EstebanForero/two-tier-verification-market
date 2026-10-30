# Data sources and licenses (checked 2026-10-30)

| Source | URL | License (from) | Used? | Pinned commit |
|---|---|---|---|---|
| DeFiHackLabs | https://github.com/SunWeb3Sec/DeFiHackLabs | Apache-2.0 (repo LICENSE file). Note: individual PoC .sol files carry `SPDX: UNLICENSED` headers; we copy **no PoC code**, only metadata (path, date, title text, explorer address). | Yes | d4bd931e758a375ed7fcecf52322dfeab54f8c0d |
| SolidiFI-benchmark | https://github.com/smartbugs/SolidiFI-benchmark | MIT, Copyright (c) 2020 UBC (repo LICENSE). LICENSE also states the original contracts were taken from Etherscan and "retain their original licenses" — so we store only file paths + injected-bug locations, **no contract source**. | Yes | 4b0573e1b3f7031396de6f48f7f3e7380222ad3a |
| Code4rena reports / `code-423n4/*-findings` repos | https://docs.code4rena.com/legal/terms-of-service | Findings repos have **no LICENSE** (GitHub API: license=null). ToS §8(e) grants only a personal/internal license; §8(g) forbids automated scraping/bulk download; §8(h) forbids building derived datasets for ML training/evaluation without a written agreement. | **No — excluded** | — |
| Uniswap v3 deployment docs | https://docs.uniswap.org/contracts/v3/reference/deployments/ethereum-deployments | No content license checked; we take only public contract addresses (facts), no text/code. | Yes (presumed-safe, 5 rows) | live page at build time |
| safe-global/safe-deployments v1.3.0 | https://github.com/safe-global/safe-deployments | MIT (repo LICENSE) | Yes (presumed-safe, 2 rows) | main at build time |

## Audit-label sources reviewed 2026-10-30 (round 2)

| Source | License / terms (evidence) | Redistribution | Derived dataset | ML use | Verdict |
|---|---|---|---|---|---|
| DAppSCAN (https://github.com/InPlusLab/DAppSCAN) | **No license.** No LICENSE file in repo root (contents: README, xlsx, DAppSCAN-source/-bytecode submodules); GitHub API `license: null`; README has no license/terms text. → all rights reserved by default. Its labels are also extracted from third-party audit firms' reports. | Not granted | Not granted | Not granted | **Excluded.** Could be re-checked if authors add a license or grant permission. |
| SmartBugs-wild (https://github.com/smartbugs/smartbugs-wild) | **Apache-2.0** (repo LICENSE; GitHub API spdx Apache-2.0). Contracts are Etherscan source downloads (original licenses apply to code). | Yes (Apache-2.0, with notice) | Yes | Yes (Apache-2.0 has no field-of-use limit) | **Not added: contains no audit labels** — 47,398 unlabeled contracts; vulnerability results live in smartbugs-results and are static-analysis tool outputs, not audit findings. Also SmartBugs data is owned by Verification Researcher's branch. |
| Solodit (https://solodit.cyfrin.io/terms-of-service, last updated 2025-12-17) | §4: may use, copy, create and distribute derivative works ("enriched datasets"), and "train, fine-tune, or benchmark machine learning models"; attribution required ("Data from Solodit"). §5.1: no redistribution of raw/unmodified data, bulk exports or mirroring. §5.2: no competing vulnerability-data API. §3.2: API key required. | Raw: **No**; derived: yes | **Yes**, with attribution | **Yes**, with attribution | **Permitted (derived metadata only)**. `scripts/build_solodit.py` written; stores no finding text. **Not run: needs a Solodit account API key (`SOLODIT_API_KEY`)** — 0 rows added. Response field names are taken from third-party client docs and must be checked on first run. |
| Uniswap v2/v3 deployment docs, safe-global/safe-deployments (MIT), bgd-labs/aave-address-book (MIT, LICENSE "Copyright 2026 BGD Labs") | Addresses only | — | — | — | Used for presumed-safe candidates |
| Blockscout API (https://eth.blockscout.com/api/v2) | Public API; only used to read creation timestamp, verification flag and tx counts (facts) | — | — | — | Used for presumed-safe filters |

Attribution: any data produced by `build_solodit.py` is "Data from Solodit (https://solodit.xyz)".
