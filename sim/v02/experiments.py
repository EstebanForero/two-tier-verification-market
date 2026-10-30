import numpy as np, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
T975 = {29: 2.045229642132703}  # t_{0.975, df}; avoids scipy dependency (CI installs numpy+pytest only)
from dataclasses import replace
from core import Params, run
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30

def ci(vals):
    v = np.array(vals, float); m = v.mean(); h = T975.get(len(v)-1, 1.96)*v.std(ddof=1)/np.sqrt(len(v))
    return m, h

def sweep(name, base, grid, keys):
    rows = []
    for g in grid:
        p = replace(base, **g); res = [run(p, s) for s in range(N)]
        row = dict(g); row.update({k: ci([r[k] for r in res]) for k in keys if k in res[0]})
        rows.append(row); print(name, g, {k: f"{v[0]:.3f}±{v[1]:.3f}" for k, v in row.items() if isinstance(v, tuple)}, flush=True)
    return rows

out = {}
B = Params()
out["E1_agg"] = sweep("E1", B, [dict(agg=a, eta=e, adv_stake=s) for s in (1.0, 3.0) for a in ("median", "trimmed", "wmean", "skill") for e in (0.0, 0.1, 0.3)],
                      ["recall", "target_recall", "ml_honest", "ml_lazy", "ml_adv"])
out["E1b_noattack"] = sweep("E1b", replace(B, frac_adv=0, frac_lazy=0), [dict(agg=a, eta=0.1) for a in ("median", "trimmed")], ["recall", "target_recall"])
out["E2_rho"] = sweep("E2", replace(B, frac_adv=0.0, frac_lazy=0.2, frac_infl=0.2, eta=0.3),
                      [dict(rho_bnd=r) for r in (0.3, 0.5, 0.71, 0.9, 1.0)], ["ml_honest", "ml_infl", "ml_lazy"])
out["E3_mutant"] = sweep("E3", B, [dict(reward_scheme=s) for s in ("1/n", "geometric")], ["prov_honest", "prov_sybil", "prov_lazy", "prov_cheat", "burned"])
out["E4_selfref"] = sweep("E4", replace(B, sybil_selfref=True, ref_bonus=0.5), [dict(phi=f, bond=b) for f in (1.0, 0.5) for b in (0.5, 1.0, 2.0)], ["selfref_profit"])
out["E5_supp"] = sweep("E5", replace(B, collude_supp=True, agg="median"),
                       [dict(defend_supp=False), dict(defend_supp=True, W_min=0.0), dict(defend_supp=True, W_min=2.0), dict(defend_supp=True, W_min=4.0), dict(defend_supp=True, W_min=4.0, bond=3.0)], ["coll_profit_per_task", "coll_excess_per_task", "coll_false_safe_survival"])
json.dump({k: [{kk: (list(vv) if isinstance(vv, tuple) else vv) for kk, vv in r.items()} for r in v] for k, v in out.items()},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results_v02.json"), "w"), indent=1)
