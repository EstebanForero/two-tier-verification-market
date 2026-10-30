"""E2 rho sweep at rho_bnd values fitted from Halmos runs (see sim/docs/rho_bnd_fit.md). Illustrative world parameters."""
import sys, json, numpy as np
from dataclasses import replace
from core import Params, run
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30; T = 2.045229642132703
B = replace(Params(), frac_adv=0.0, frac_lazy=0.2, frac_infl=0.2, eta=0.3)
grid = [0.375, 0.438, 0.5, 0.6, 0.706, 0.9, 0.921, 0.957, 0.973]
rows = []
for r in grid:
    R = [run(replace(B, rho_bnd=r), s) for s in range(N)]
    d = np.array([x["ml_infl"] - x["ml_honest"] for x in R])
    row = dict(rho_bnd=r, **{k: (float(np.mean([x[k] for x in R])), float(T*np.std([x[k] for x in R], ddof=1)/np.sqrt(N))) for k in ("ml_honest", "ml_infl", "ml_lazy")},
               infl_minus_honest=(float(d.mean()), float(T*d.std(ddof=1)/np.sqrt(N))))
    rows.append(row); print({k: (f"{v[0]:.3f}±{v[1]:.3f}" if isinstance(v, tuple) else v) for k, v in row.items()}, flush=True)
json.dump(rows, open(__file__.replace("exp_rho_fit.py", "results_rho_fit.json"), "w"), indent=1)
