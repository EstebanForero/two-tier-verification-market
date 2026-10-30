"""Lazy-prover fixes. Illustrative parameters. python3 exp_lazy.py 30"""
import sys, json, numpy as np
from dataclasses import replace
from core import Params, run
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30; T = 2.045229642132703
def ci(v): v = np.array(v, float); return float(v.mean()), float(T*v.std(ddof=1)/np.sqrt(len(v)))
rows = []
for c in (0.0, 0.1):
    for rule in ("base", "tied", "kill_required"):
        for mr in (0.3, 0.6, 0.9):
            p = replace(Params(), safe_pay_rule=rule, mutant_rate=mr, search_cost=c)
            R = [run(p, s) for s in range(N)]
            row = dict(search_cost=c, rule=rule, mutant_rate=mr)
            for k in ("prov_honest", "prov_lazy", "lazy_over_honest", "recall", "false_safe_survival"):
                row[k] = ci([r[k] for r in R])
            rows.append(row)
            print(c, rule, mr, {k: f"{v[0]:.3f}±{v[1]:.3f}" for k, v in row.items() if isinstance(v, tuple)}, flush=True)
json.dump(rows, open(__import__("pathlib").Path(__file__).with_name("results_lazy.json"), "w"), indent=1)
