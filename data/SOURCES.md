# Data sources and licenses (checked 2026-10-30)

| Source | URL | License (from) | Used? | Pinned commit |
|---|---|---|---|---|
| DeFiHackLabs | https://github.com/SunWeb3Sec/DeFiHackLabs | Apache-2.0 (repo LICENSE file). Note: individual PoC .sol files carry `SPDX: UNLICENSED` headers; we copy **no PoC code**, only metadata (path, date, title text, explorer address). | Yes | d4bd931e758a375ed7fcecf52322dfeab54f8c0d |
| SolidiFI-benchmark | https://github.com/smartbugs/SolidiFI-benchmark | MIT, Copyright (c) 2020 UBC (repo LICENSE). LICENSE also states the original contracts were taken from Etherscan and "retain their original licenses" — so we store only file paths + injected-bug locations, **no contract source**. | Yes | 4b0573e1b3f7031396de6f48f7f3e7380222ad3a |
| Code4rena reports / `code-423n4/*-findings` repos | https://docs.code4rena.com/legal/terms-of-service | Findings repos have **no LICENSE** (GitHub API: license=null). ToS §8(e) grants only a personal/internal license; §8(g) forbids automated scraping/bulk download; §8(h) forbids building derived datasets for ML training/evaluation without a written agreement. | **No — excluded** | — |
| Uniswap v3 deployment docs | https://docs.uniswap.org/contracts/v3/reference/deployments/ethereum-deployments | No content license checked; we take only public contract addresses (facts), no text/code. | Yes (presumed-safe, 5 rows) | live page at build time |
| safe-global/safe-deployments v1.3.0 | https://github.com/safe-global/safe-deployments | MIT (repo LICENSE) | Yes (presumed-safe, 2 rows) | main at build time |
