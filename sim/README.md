# sim

Stage 4: mechanism simulation.

- v0.1: `python sim/sim.py`
- v0.2 (prover tier, refutation window, LOO scoring, aggregators): `python sim/v02/experiments.py 30` regenerates `sim/v02/results_v02.json` (about 1 minute, numpy only). Write-up: `docs/results_v02.md`. All numbers are simulation outputs under illustrative parameters.
- Tests: `pytest -q sim`
- Docs: `docs/`
