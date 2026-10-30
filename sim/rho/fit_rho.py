"""Fit bounded-check miss rate and rho_bnd weight from Halmos runs. python3 fit_rho.py"""
import csv, json, numpy as np
from collections import defaultdict
from statistics import NormalDist
from pathlib import Path
import sys
CSV = Path(sys.argv[1] if len(sys.argv) > 1 else "/workspace/research/two-tier-market/data/rho_bnd_runs.csv")  # data lives outside the repo
z = NormalDist().inv_cdf(0.975)
def wilson(x, n):
    if n == 0: return (np.nan, np.nan, np.nan)
    p = x/n; den = 1+z*z/n; c = (p+z*z/(2*n))/den; h = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return (p, max(0, c-h), min(1, c+h))
rows = list(csv.DictReader(open(CSV)))
out = {"n_rows": len(rows), "by_k": {}}
ks = sorted({int(r["bound_k"]) for r in rows})
for k in ks:
    b = [r for r in rows if int(r["bound_k"]) == k and r["ground_truth_buggy"] == "1"]
    f = [r for r in rows if int(r["bound_k"]) == k and r["ground_truth_buggy"] == "0"]
    cnt = lambda R, v: sum(r["verdict"] == v for r in R)
    bs, bc, bt = cnt(b, "safe"), cnt(b, "cex"), cnt(b, "timeout") + cnt(b, "error")
    fs, fc, ft = cnt(f, "safe"), cnt(f, "cex"), cnt(f, "timeout") + cnt(f, "error")
    d = dict(buggy=dict(safe=bs, cex=bc, nores=bt), fixed=dict(safe=fs, cex=fc, nores=ft),
             miss_excl=wilson(bs, bs+bc),            # timeouts dropped
             miss_as_miss=wilson(bs+bt, bs+bc+bt),   # timeout = no cex = miss (operational)
             spec_excl=wilson(fs, fs+fc))
    # rho weight = P(truly safe | bounded "safe") among runs that returned safe
    d["ppv_safe_sample"] = wilson(fs, fs+bs)
    out["by_k"][k] = d
    print(k, d)
# depth step model check: verdict==cex iff k>=depth, among completed buggy runs
comp = [r for r in rows if r["ground_truth_buggy"] == "1" and r["verdict"] in ("safe", "cex")]
agree = sum((r["verdict"] == "cex") == (int(r["bound_k"]) >= int(r["bug_min_depth"])) for r in comp)
out["step_model_agreement"] = [agree, len(comp)]
print("step model agreement", agree, "/", len(comp))
# Bayes map to sim rho at base rate pi, given miss m and spec s=1 (no false cex)
def rho_w(pi, m, s=1.0): return (1-pi)*s/((1-pi)*s + pi*m)
out["rho_weight_pi"] = {}
for pi in (0.1, 0.3, 5/8):
    for k in ks:
        m = out["by_k"][k]["miss_as_miss"]
        out["rho_weight_pi"][f"pi={pi:.3f},k={k}"] = [rho_w(pi, m[0]), rho_w(pi, m[2]), rho_w(pi, m[1])]
json.dump(out, open(Path(__file__).with_name("rho_fit.json"), "w"), indent=1)
for kk, v in out["rho_weight_pi"].items(): print(kk, [round(x, 3) for x in v])
