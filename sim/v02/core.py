"""v0.2 two-tier market simulation core. All parameters ILLUSTRATIVE.
Anchors from repo data (verification/pipeline/results_halmos.json, 17 Halmos checks on toy targets):
FV detect ~0.8 (8/10 buggy variants killed), P(safe | pass) ~5/7 = 0.71."""
import numpy as np
from dataclasses import dataclass, field

def logit(p): return np.log(p / (1 - p))
def sigm(z): return 1 / (1 + np.exp(-z))
def brier(p, y): return -(y - p) ** 2

# ---------- aggregation ----------
def agg_median(P, stake): return np.median(P, axis=0)

def agg_trimmed_capped(P, stake, cap=1.0, trim=0.25):
    """Stake-capped weights, weighted log-odds mean after trimming `trim` weight mass from each tail."""
    w = np.minimum(stake, cap)[:, None] * np.ones_like(P)
    L = logit(P); idx = np.argsort(L, axis=0)
    Ls = np.take_along_axis(L, idx, 0); ws = np.take_along_axis(w, idx, 0)
    c = np.cumsum(ws, 0) / ws.sum(0); lo = c - ws / ws.sum(0)
    keep = np.clip(np.minimum(c, 1 - trim) - np.maximum(lo, trim), 0, None) * ws.sum(0)
    return sigm((keep * Ls).sum(0) / np.maximum(keep.sum(0), 1e-12))

def agg_skill_trimmed(P, stake, skill, cap=1.0, trim=0.25):
    """Extension: stake cap x audit-set skill weight (past epochs)."""
    return agg_trimmed_capped(P, np.minimum(stake, cap) * skill, cap=np.inf, trim=trim)

def agg_wmean(P, stake):
    """Uncapped stake-weighted log-odds mean (baseline that stake caps protect against)."""
    return sigm((stake[:, None]*logit(P)).sum(0)/stake.sum())

AGG = {"median": agg_median, "trimmed": agg_trimmed_capped, "wmean": agg_wmean}

@dataclass
class Params:
    n_tasks: int = 1000; epochs: int = 10; base_rate: float = 0.1; target_frac: float = 0.1
    n_ml: int = 20; frac_adv: float = 0.4; frac_lazy: float = 0.2; frac_infl: float = 0.0
    adv_stake: float = 1.0; deflate: float = 0.3; infl: float = 1.5
    agg: str = "trimmed"; eta: float = 0.1; budget_frac: float = 0.15
    detect: float = 0.8; rho_bnd: float = 0.71
    # prover tier
    n_prov: int = 10; prov_per_task: int = 3; frac_lazy_prov: float = 0.2; frac_cheat_prov: float = 0.1
    sybil_clones: int = 3; mutant_rate: float = 0.3; J: float = 1.0; reward_scheme: str = "geometric"
    beta_cex: float = 1.0; beta_safe: float = 0.3; theta: float = 2.0; bond: float = 1.0; cheat_rate: float = 0.2
    # window
    W0: float = 1.0; kappa_W: float = 3.0; W_min: float = 0.0; lam: float = 0.7; phi: float = 0.5
    ref_bonus: float = 0.0
    search_cost: float = 0.0  # effort cost per routed task searched (honest/cheat/Sybil); 0 reproduces v0.2
    safe_pay_rule: str = "base"  # base | tied | kill_required
    collude_supp: bool = False; defend_supp: bool = False; sybil_selfref: bool = False

def mutant_payout(k_honest, k_attacker_ids, J, scheme):
    """Per-identity payout on one killed mutant: k total killer identities."""
    k = k_honest + k_attacker_ids
    if k == 0: return 0.0
    total = J if scheme == "1/n" else J / 2 ** (k - 1)
    return total / k

def run(p: Params, seed=0):
    rng = np.random.default_rng(seed)
    n_adv, n_lazy, n_infl = int(p.frac_adv*p.n_ml), int(p.frac_lazy*p.n_ml), int(p.frac_infl*p.n_ml)
    types = np.array(["adv"]*n_adv + ["lazy"]*n_lazy + ["infl"]*n_infl + ["honest"]*(p.n_ml-n_adv-n_lazy-n_infl))
    stake = np.where(types == "adv", p.adv_stake, 1.0)
    ml_pay = np.zeros(p.n_ml); n_scored = 0
    # prover types: 0 = honest, 1 = lazy, 2 = cheat (posts invalid CEX), last honest prover is a Sybil (clones kills)
    n_lp, n_cp = int(p.frac_lazy_prov*p.n_prov), int(p.frac_cheat_prov*p.n_prov)
    ptype = np.array([1]*n_lp + [2]*n_cp + [0]*(p.n_prov-n_lp-n_cp)); sybil = p.n_prov - 1
    prov_pay = np.zeros(p.n_prov); prov_kills = np.zeros(p.n_prov)
    st = dict(bugs=0, found=0, tbugs=0, tfound=0, fs_posted=0, fs_survive=0,
              burned=0.0, coll_profit=0.0, coll_tasks=0, selfref_profit=0.0)
    for _ in range(p.epochs):
        y = rng.random(p.n_tasks) < p.base_rate
        tgt = rng.random(p.n_tasks) < p.target_frac
        sig = np.clip(p.base_rate + 0.6*(y - p.base_rate) + rng.normal(0, .15, p.n_tasks), .01, .99)
        P = np.empty((p.n_ml, p.n_tasks))
        for i, t in enumerate(types):
            b = np.clip(sig + rng.normal(0, .05, p.n_tasks), .01, .99)
            P[i] = {"lazy": np.full(p.n_tasks, p.base_rate),
                    "adv": np.where(tgt, b*p.deflate, b),
                    "infl": np.clip(b*p.infl, .01, .99)}.get(t, b)
        P = np.clip(P, .01, .99)
        skill = np.exp(np.clip(50*ml_pay/max(n_scored, 1), -20, 0)) if n_scored else np.ones(p.n_ml)
        aggf = (lambda PP, ss, sk=skill: agg_skill_trimmed(PP, ss, sk)) if p.agg == "skill" else AGG[p.agg]
        q = aggf(P, stake)
        # routing: exploit share by q, exploration share uniform (= audit set, fully resolved)
        B = p.budget_frac * p.n_tasks
        explore = rng.random(p.n_tasks) < p.eta * p.budget_frac
        exploit = rng.random(p.n_tasks) < np.clip((1-p.eta)*B*q/q.sum(), 0, 1)
        routed = explore | exploit
        # ---------- prover tier ----------
        mut = rng.random(p.n_tasks) < p.mutant_rate
        cex_found = np.zeros(p.n_tasks, bool)
        for x in np.flatnonzero(routed):
            team = rng.choice(p.n_prov, p.prov_per_task, replace=False); poster_killed = False
            searchers = team[ptype[team] != 1]
            prov_pay[searchers] -= p.search_cost
            hit_bug = searchers[rng.random(len(searchers)) < p.detect] if y[x] else []
            hit_mut = searchers[rng.random(len(searchers)) < p.detect] if mut[x] else []
            if len(hit_bug):
                cex_found[x] = True
                ids = len(hit_bug) + ((p.sybil_clones-1) if sybil in hit_bug else 0)
                for k in hit_bug:
                    mult = p.sybil_clones if k == sybil else 1
                    prov_pay[k] += mult * mutant_payout(ids, 0, p.beta_cex, p.reward_scheme)
            if len(hit_mut):
                ids = len(hit_mut) + ((p.sybil_clones-1) if sybil in hit_mut else 0)
                for k in hit_mut:
                    mult = p.sybil_clones if k == sybil else 1
                    prov_pay[k] += mult * mutant_payout(ids, 0, p.J, p.reward_scheme); prov_kills[k] += 1
                    if k == team[0]: poster_killed = True
            for k in team[ptype[team] == 2]:                       # invalid certificate: always caught by checker
                if rng.random() < p.cheat_rate: prov_pay[k] -= p.bond; st["burned"] += p.bond
            if not cex_found[x]:                                    # BSAFE claim -> refutation window
                qx = q[x]
                W = p.W0*(1 + p.kappa_W*qx); W = max(W, p.W_min)
                q_pay = qx
                pay_safe = p.beta_safe*(1-q_pay)**p.theta
                if p.safe_pay_rule == "tied" and mut[x] and not poster_killed: pay_safe = 0.0   # missed a planted mutant on this contract
                if p.safe_pay_rule == "kill_required" and not poster_killed: pay_safe = 0.0     # no kill on this contract, no BSAFE pay
                refuted = y[x] and rng.random() < 1 - np.exp(-p.lam*W)
                if y[x]: st["fs_posted"] += 1; st["fs_survive"] += (not refuted)
                poster = team[0]
                if refuted:
                    prov_pay[poster] -= p.bond; st["burned"] += (1-p.phi)*p.bond; cex_found[x] = True
                else:
                    prov_pay[poster] += pay_safe
        # q-suppression collusion: deflating screeners + a colluding prover that posts BSAFE on every target
        if p.collude_supp:
            if p.defend_supp:   # payout/window use a skill-weighted, stake-capped trimmed snapshot taken before the claim
                qd = agg_skill_trimmed(P, stake, skill)
                Wmin = p.W_min
            else:
                qd, Wmin = q, 0.0
            hon = types == "honest"; qh = np.mean(P[hon], 0) if hon.any() else q   # counterfactual honest forecast
            def ev(qq, Wm, yy):
                W = np.maximum(p.W0*(1 + p.kappa_W*qq), Wm); pr = yy*(1 - np.exp(-p.lam*W))
                return (1-pr)*p.beta_safe*(1-qq)**p.theta - pr*p.bond
            T = tgt
            st["coll_excess"] = st.get("coll_excess", 0) + (ev(qd[T], Wmin, y[T]) - ev(qh[T], 0.0, y[T])).sum()
            for x in np.flatnonzero(tgt):
                W = max(p.W0*(1 + p.kappa_W*qd[x]), Wmin)
                ref = y[x] and rng.random() < 1 - np.exp(-p.lam*W)
                st["coll_tasks"] += 1
                st["coll_profit"] += -p.bond if ref else p.beta_safe*(1-qd[x])**p.theta
                if y[x]: st["c_bug"] = st.get("c_bug", 0) + 1; st["c_surv"] = st.get("c_surv", 0) + (not ref)
        # Sybil self-refutation: attacker who holds a CEX posts BSAFE (A) and refutes it (B)
        if p.sybil_selfref:
            n_att = int((cex_found & routed).sum() * 0.1)
            st["selfref_profit"] += n_att * (p.phi*p.bond + p.ref_bonus - p.bond)
        st["bugs"] += y.sum(); st["found"] += (cex_found & y).sum()
        st["tbugs"] += (y & tgt).sum(); st["tfound"] += (cex_found & y & tgt).sum()
        # ---------- ML settlement on audit set, leave-one-out reference ----------
        A = np.flatnonzero(explore)
        if len(A):
            ya = (y[A] & cex_found[A]).astype(float)          # observed label
            rho = np.where(ya == 1, 1.0, p.rho_bnd)            # bounded-safe resolutions get partial weight
            for i in range(p.n_ml):
                others = np.delete(np.arange(p.n_ml), i)
                ref = (agg_skill_trimmed(P[others][:, A], stake[others], skill[others]) if p.agg == "skill"
                       else AGG[p.agg](P[others][:, A], stake[others]))
                ml_pay[i] += (rho * (brier(P[i, A], ya) - brier(ref, ya))).sum()
            n_scored += len(A)
    out = dict(recall=st["found"]/max(st["bugs"], 1), target_recall=st["tfound"]/max(st["tbugs"], 1),
               false_safe_survival=st["fs_survive"]/max(st["fs_posted"], 1),
               burned=st["burned"], selfref_profit=st["selfref_profit"],
               coll_profit_per_task=st["coll_profit"]/max(st["coll_tasks"], 1),
               coll_excess_per_task=st.get("coll_excess", 0)/max(st["coll_tasks"], 1),
               coll_false_safe_survival=st.get("c_surv", 0)/max(st.get("c_bug", 0), 1))
    for t in ["honest", "lazy", "adv", "infl"]:
        if (types == t).any(): out[f"ml_{t}"] = ml_pay[types == t].mean()
    honest_p = (ptype == 0); honest_p[sybil] = False
    out.update(lazy_over_honest=(prov_pay[ptype == 1].mean()/prov_pay[honest_p].mean()) if n_lp else np.nan,
               prov_honest=prov_pay[honest_p].mean(), prov_sybil=prov_pay[sybil],
               prov_lazy=prov_pay[ptype == 1].mean() if n_lp else np.nan,
               prov_cheat=prov_pay[ptype == 2].mean() if n_cp else np.nan)
    return out
