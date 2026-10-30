"""Spot-check detectability: closed forms + Monte Carlo best response. Illustrative parameters.
Agent sees a detector score z per task: planted spot check (mutant) ~ N(delta,1), real ~ N(0,1),
AUC = Phi(delta/sqrt 2). Per task the agent chooses full effort (cost c) or shirk.
  real task:  shirking saves G = c - dR   (dR = expected real reward lost by not searching)
  spot check: full effort kills w.p. d; an unkilled spot check costs penalty P (and forgoes J);
              shirking vs full loses D = d(J+P) - c.
python3 spotcheck.py 30"""
import sys, json, numpy as np
from statistics import NormalDist
N01 = NormalDist(); T = 2.045229642132703

def delta_of_auc(auc): return np.sqrt(2) * N01.inv_cdf(auc)

def K(s, P, c, G, d, J): return s * (d * (J + P) - c) / ((1 - s) * G)

def shirk_threshold(auc, s, P, c, G, d, J):
    """Best response (binormal): shirk iff z < z*. Returns z* (−inf if never shirk)."""
    k = K(s, P, c, G, d, J); dl = delta_of_auc(auc)
    if k <= 0: return np.inf
    if dl == 0: return np.inf if k < 1 else -np.inf
    return dl / 2 - np.log(k) / dl

def shirk_frac_real(auc, **kw):
    z = shirk_threshold(auc, **kw); return 0.0 if z == -np.inf else (1.0 if z == np.inf else N01.cdf(z))

def P_min_eps(auc, eps, s, c, G, d, J):
    """Min penalty so the best response shirks on at most eps of real tasks (binormal)."""
    dl = delta_of_auc(auc); req_K = np.exp(dl**2 / 2 - dl * N01.inv_cdf(eps)) if dl > 0 else 1.0
    return max(0.0, (c + req_K * G * (1 - s) / s) / d - J)

def s_min_eps(auc, eps, P, c, G, d, J):
    dl = delta_of_auc(auc); req_K = np.exp(dl**2 / 2 - dl * N01.inv_cdf(eps)) if dl > 0 else 1.0
    D = d * (J + P) - c
    return np.inf if D <= 0 else req_K * G / (req_K * G + D)

def P_min_binary(auc, s, c, G, d, J):
    """Binary flag (TPR t, FPR f, AUC=(1+t-f)/2). Lambda=(1-f)/(1-t) >= 1/(2(1-AUC)) (equality at f=0; unbounded as t->1),
    so this is a LOWER bound on the required penalty."""
    lam = 1 / (2 * (1 - auc)); return max(0.0, (c + lam * G * (1 - s) / s) / d - J)

def _sample(auc, s, d, n, rng):
    dl = delta_of_auc(auc); spot = rng.random(n) < s
    return spot, rng.normal(0, 1, n) + dl * spot, rng.random(n) < d

def _gain(tau, spot, z, kill, P, c, G, J):
    sh = z < tau; real = ~spot
    g = (G * (sh & real)).sum() + np.where(sh & spot, -P - (np.where(kill, J, -P) - c), 0).sum()
    return g / len(z), (sh & real).sum() / max(real.sum(), 1)

def mc(auc, s, P, c, G, d, J, n=20000, seed=0, grid=np.linspace(-4, 6, 201)):
    """Agent picks the best threshold 'shirk iff z<tau' on a training sample (an agent that has learned
    the detector), then is evaluated on an independent sample. Returns (gain/task vs full effort, shirk frac on real)."""
    rng = np.random.default_rng(seed)
    tr = _sample(auc, s, d, n, rng); te = _sample(auc, s, d, n, rng)
    taus = np.concatenate([[-np.inf], grid, [np.inf]])
    tau = max(taus, key=lambda t: _gain(t, *tr, P, c, G, J)[0])
    return _gain(tau, *te, P, c, G, J)

if __name__ == "__main__":
    NS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    base = dict(c=0.1, G=0.05, d=0.8, J=1.0); s = 0.1; eps = 0.05
    aucs = [0.5, 0.55, 0.6, 0.7, 0.8, 0.9, 0.95]
    P_naive = 0.0   # AUC-blind design: at AUC=0.5, P=0 already gives K=1.56 (IC with 56% slack)
    out = dict(params=dict(base, s=s, eps=eps, P_naive=P_naive), rows=[])
    for a in aucs:
        Pe = P_min_eps(a, eps, s, **base)
        r = dict(auc=a, P_min_eps=Pe, P_min_binary=P_min_binary(a, s, **base),
                 s_min_eps_at_P5=s_min_eps(a, eps, 5.0, **base),
                 shirk_naive_closed=shirk_frac_real(a, s=s, P=P_naive, **base),
                 shirk_eps_closed=shirk_frac_real(a, s=s, P=Pe, **base))
        for tag, P in (("naive", P_naive), ("eps", Pe)):
            res = [mc(a, s, P, seed=k, **base) for k in range(NS)]
            for j, name in ((0, "gain_per_task"), (1, "shirk_frac")):
                v = np.array([x[j] for x in res]); r[f"mc_{tag}_{name}"] = (float(v.mean()), float(T * v.std(ddof=1) / np.sqrt(NS)))
        out["rows"].append(r)
        print({k: (f"{v[0]:.4f}±{v[1]:.4f}" if isinstance(v, tuple) else round(v, 4)) for k, v in r.items()}, flush=True)
    json.dump(out, open(__import__("pathlib").Path(__file__).with_name("results_spotcheck.json"), "w"), indent=1)
