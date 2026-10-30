# Two-Tier Verification Market for EVM Bytecode

Research project (Esteban Forero): a decentralized market where **ML screeners** stake on calibrated bug probabilities (paid by proper scoring rules on a random audit set) and **formal-verification provers** submit checkable certificates (counterexamples slashable immediately; bounded "safe" claims paid via a refutation window). ML scores route a fixed FV budget, with an η random-routing floor and robust aggregation against manipulation.

## Layout
- `contracts/` Foundry contracts (Stage 5)
- `ml/` screener models (Stage 3)
- `fv/` Halmos/hevm pipeline + certificate checking (Stage 2)
- `data/` dataset build scripts (Stage 1)
- `sim/` mechanism simulation (Stage 4)
- `experiments/` end-to-end experiments (Stage 6)
- `paper/`, `related-work/` Typst paper + bibliography (Stage 7)

## Roadmap
| Stage | Weeks | Status |
|---|---|---|
| 0 Infra & CI | 0–1 | done |
| 1 Dataset v1 | 1–4 | next |
| 2 FV pipeline & certificate costs | 2–7 | started |
| 3 ML screeners | 4–11 | – |
| 4 Mechanism sim v0.2→v1.0 | 1–12 | v0.1 |
| 5 Solidity contracts + Foundry tests | 6–14 | – |
| 6 End-to-end experiments | 12–18 | – |
| 7 Paper → arXiv | 18–24 | skeleton |

Full plan: [PLAN.md](PLAN.md). License: MIT.
