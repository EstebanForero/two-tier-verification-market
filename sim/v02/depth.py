"""Depth-dependent bounded-check model for rho_bnd (v0.3).

Fitted rule (docs/rho_bnd_fit.md, 23/23 completed Halmos runs): a bounded check at bound k on a buggy
contract with minimum bug depth D yields a counterexample iff k >= D AND the run completes.

  miss(k)   = 1 - detect * (1 - P(D > k)) * p_complete(k)
  rho(k)    = P(truly safe | no cex at k) = (1-pi) / ((1-pi) + pi * miss(k))        (spec = 1: no false cex observed)

The sim treats every task without a cex as a bounded-"safe" resolution, so timeouts count as "no cex"
(on clean contracts too, which cancels in rho when completion does not depend on bugginess).

Empirical CSV schema (Verification Researcher's per-mutant rerun), header names case-insensitive:
  depth column (required, first match): depth, bug_depth, bug_min_depth, min_depth, min_k, first_cex_k, cex_k
      integer >= 1; blank / inf / none / na / nan / ">K" (censored: not found up to K)  -> treated as D = inf
  buggy filter (optional): ground_truth_buggy, buggy, is_buggy  -> keep rows with 1/true/yes
  weight (optional): weight, count, n  -> row weight (default 1)
"""
import csv, math, numpy as np

class Geometric:
    """P(D = d) = (1-g) g^(d-1), d >= 1;  P(D > k) = g^k.  Larger g = heavier tail."""
    def __init__(self, g=0.5): assert 0 <= g < 1; self.g = g
    def sf(self, k): return self.g ** k
    def sample(self, rng, n): return rng.geometric(1 - self.g, n) if self.g > 0 else np.ones(n, int)

class DiscretePareto:
    """P(D > k) = k^(-alpha) for k >= 1 (D >= 1); polynomial tail."""
    def __init__(self, alpha=1.0): assert alpha > 0; self.a = alpha
    def sf(self, k): return 1.0 if k < 1 else float(k) ** (-self.a)
    def sample(self, rng, n): return np.ceil((1 - rng.random(n)) ** (-1 / self.a))  # X Pareto(1,a): P(ceil X > k) = P(X > k) = k^-a

class Empirical:
    def __init__(self, depths, weights=None):
        self.d = np.asarray(depths, float); self.w = np.ones(len(self.d)) if weights is None else np.asarray(weights, float)
        assert len(self.d) and self.w.sum() > 0; self.w = self.w / self.w.sum()
    def sf(self, k): return float(self.w[self.d > k].sum())
    def sample(self, rng, n): return rng.choice(self.d, size=n, p=self.w)

DEPTH_COLS = ("depth", "bug_depth", "bug_min_depth", "min_depth", "min_k", "first_cex_k", "cex_k")
BUGGY_COLS = ("ground_truth_buggy", "buggy", "is_buggy"); WEIGHT_COLS = ("weight", "count", "n")

def _parse_depth(v):
    v = (v or "").strip().lower()
    if v in ("", "inf", "none", "na", "nan", "null") or v.startswith(">"): return math.inf
    d = float(v); assert d >= 1, f"depth must be >= 1, got {v}"; return d

def load_depth_csv(path):
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows: raise ValueError("empty depth CSV")
    norm = {k.strip().lower(): k for k in rows[0].keys()}
    pick = lambda names: next((norm[c] for c in names if c in norm), None)
    dc, bc, wc = pick(DEPTH_COLS), pick(BUGGY_COLS), pick(WEIGHT_COLS)
    if dc is None: raise ValueError(f"no depth column; expected one of {DEPTH_COLS}, got {list(norm)}")
    keep = [r for r in rows if bc is None or str(r[bc]).strip().lower() in ("1", "true", "yes", "y")]
    return Empirical([_parse_depth(r[dc]) for r in keep], [float(r[wc]) for r in keep] if wc else None)

def step_timeout(k_max):
    """Runs complete iff k <= k_max (fitted: ~6 tx at 30-60 s solver timeouts)."""
    return lambda k: 1.0 if k <= k_max else 0.0

def no_timeout(k): return 1.0

def miss_rate(k, dist, p_complete=no_timeout, detect=1.0):
    return 1 - detect * (1 - dist.sf(k)) * p_complete(k)

def rho_bayes(base_rate, k, dist, p_complete=no_timeout, detect=1.0):
    m = miss_rate(k, dist, p_complete, detect)
    return (1 - base_rate) / ((1 - base_rate) + base_rate * m)
