"""v0.3 sweep: where the inflator tilt bites, by bound k, depth-distribution tail, timeouts and base rate.
Illustrative world parameters (E2 base: 20% inflators, 20% lazy, eta=0.3; detect=1 = fitted rule). python3 exp_depth.py 30"""
import sys, json, pathlib, numpy as np
from dataclasses import replace
from core import Params, run
import depth as D
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30; T = 2.045229642132703
B = replace(Params(), frac_adv=0.0, frac_lazy=0.2, frac_infl=0.2, eta=0.3, rho_mode="depth", detect=1.0)
dists = {"geom0.3": D.Geometric(0.3), "geom0.5": D.Geometric(0.5), "geom0.7": D.Geometric(0.7),
         "geom0.85": D.Geometric(0.85), "pareto1.0": D.DiscretePareto(1.0), "pareto0.5": D.DiscretePareto(0.5)}
tos = {"none": None, "step6": D.step_timeout(6)}
rows = []
for pi in (0.1, 0.3, 0.5):
    for dn, dd in dists.items():
        for tn, tm in tos.items():
            for k in (1, 2, 3, 4, 6, 8):
                p = replace(B, base_rate=pi, depth_dist=dd, p_complete=tm, bound_k=k)
                R = [run(p, s) for s in range(N)]
                d = np.array([r["ml_infl"] - r["ml_honest"] for r in R]); rec = np.array([r["recall"] for r in R])
                row = dict(base_rate=pi, dist=dn, timeout=tn, k=k, rho=R[0]["rho_safe"], sf_k=dd.sf(k),
                           infl_minus_honest=(float(d.mean()), float(T*d.std(ddof=1)/np.sqrt(N))),
                           recall=(float(rec.mean()), float(T*rec.std(ddof=1)/np.sqrt(N))))
                rows.append(row)
                print(pi, dn, tn, k, f"rho={row['rho']:.3f}", "dI-H=%.3f±%.3f" % row["infl_minus_honest"], "rec=%.3f" % row["recall"][0], flush=True)
json.dump(rows, open(pathlib.Path(__file__).with_name("results_depth.json"), "w"), indent=1)
