# sim

Stage 4: mechanism simulation.

- v0.1: `python sim/sim.py`
- v0.2 (prover tier, refutation window, LOO scoring, aggregators): `python sim/v02/experiments.py 30` regenerates `sim/v02/results_v02.json` (about 1 minute, numpy only). Write-up: `docs/results_v02.md`. All numbers are simulation outputs under illustrative parameters.
- Tests: `pytest -q sim`
- Docs: `docs/`

## v0.2.1 / v0.2.2 additions
- `Params.safe_pay_rule` ∈ {`base` (default, reproduces v0.2), `tied` (recommended: BSAFE pay zeroed if the poster missed a planted mutant on that contract), `kill_required`}. `Params.search_cost` defaults to 0. `tied` is not the default because it changes the v0.2 E3 prover payoffs. Analysis: `docs/lazy_prover.md` (`v02/exp_lazy.py`).
- `v02/spotcheck.py`: closed-form spot-check IC vs probe AUC (binary Λ, binormal P_ε / s_ε) and a Monte Carlo best-response check. See `docs/spotcheck_auc.md`.
- `rho/fit_rho.py <csv>`: Wilson-CI fit of the bounded-check miss rate and the ρ_bnd weight from Halmos runs (data lives outside the repo). `v02/exp_rho_fit.py` reruns E2 at the fitted ρ. See `docs/rho_bnd_fit.md`.

## v0.3: depth-dependent rho_bnd
`Params.rho_mode="depth"` derives ρ through Bayes from `base_rate`, `bound_k`, `depth_dist` and `p_complete` (`v02/depth.py`). The default `"flat"` mode reproduces v0.2 exactly. `depth.load_depth_csv` loads per-mutant depths (schema in `docs/rho_depth.md`). Sweep: `v02/exp_depth.py`.
