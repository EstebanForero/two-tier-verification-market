"""Minimal agent-based skeleton for the two-tier market. Illustrative only.
Run: python3 sim.py   (numpy only)"""
import numpy as np, argparse

def brier(p, y): return -(y - p) ** 2

def run(n_tasks=2000, base_rate=0.1, n_ml=20, frac_adv=0.2, deflate=0.5,
        eta=0.2, budget_frac=0.15, fv_detect=0.8, epochs=20, seed=0):
    rng = np.random.default_rng(seed)
    types = np.array(["honest"] * n_ml, dtype=object)
    n_adv = int(frac_adv * n_ml); types[:n_adv] = "adversarial"
    types[n_adv:n_adv + n_ml // 5] = "lazy"
    pay = np.zeros(n_ml); found = 0; bugs_total = 0; target_found = 0; target_bugs = 0
    for _ in range(epochs):
        y = rng.random(n_tasks) < base_rate
        signal = np.clip(base_rate + 0.6 * (y - base_rate) + rng.normal(0, 0.15, n_tasks), .01, .99)
        target = rng.random(n_tasks) < 0.1   # adversary wants these unexamined
        P = np.empty((n_ml, n_tasks))
        for i, t in enumerate(types):
            noisy = np.clip(signal + rng.normal(0, .05, n_tasks), .01, .99)
            if t == "lazy": P[i] = base_rate
            elif t == "adversarial": P[i] = np.where(target, noisy * deflate, noisy)
            else: P[i] = noisy
        q = np.median(P, axis=0)                      # trimmed/robust aggregate
        B = budget_frac * n_tasks
        g = q / q.sum()
        pi = np.clip((1 - eta) * B * g + eta * B / n_tasks, 1e-6, 1)
        routed = rng.random(n_tasks) < pi
        caught = routed & y & (rng.random(n_tasks) < fv_detect)
        found += caught.sum(); bugs_total += y.sum()
        target_found += (caught & target).sum(); target_bugs += (y & target).sum()
        # ML scored only on uniform audit subset (IPW, w=1/eta-share) -> unbiased
        audit = rng.random(n_tasks) < eta * budget_frac
        ref = q
        pay += (brier(P[:, audit], y[audit]) - brier(ref[audit], y[audit])).sum(1)
    return dict(recall=found / bugs_total, target_recall=target_found / max(target_bugs, 1),
                mean_pay={t: float(pay[types == t].mean()) for t in set(types)})

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    for eta in (0.0, 0.1, 0.3):
        for frac_adv in (0.0, 0.4, 0.6):
            r = run(eta=eta, frac_adv=frac_adv, seed=a.seed)
            print(f"eta={eta} adv={frac_adv}: recall={r['recall']:.2f} "
                  f"target_recall={r['target_recall']:.2f} pay={ {k: round(v,2) for k,v in r['mean_pay'].items()} }")
