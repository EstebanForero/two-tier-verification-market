"""Tests for sim v0.2 (sim/v02/core.py)."""
import sys, pathlib
from dataclasses import replace
import numpy as np
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "v02"))
import core
from core import Params, run, brier, agg_median, agg_trimmed_capped, agg_wmean, mutant_payout


# ---------- scoring-rule properness ----------
@pytest.mark.parametrize("q", [0.05, 0.1, 0.3, 0.5, 0.8, 0.97])
def test_brier_strictly_proper(q):
    grid = np.linspace(0.001, 0.999, 999)
    exp = q * brier(grid, 1) + (1 - q) * brier(grid, 0)
    assert abs(grid[np.argmax(exp)] - q) < 1e-3
    assert np.all(exp[np.abs(grid - q) > 0.01] < exp.max())

def test_report_independent_reference_keeps_properness():
    q, r = 0.3, 0.6  # subtracting S(r, y) with r independent of the report shifts but does not move the argmax
    grid = np.linspace(0.001, 0.999, 999)
    exp = q * (brier(grid, 1) - brier(r, 1)) + (1 - q) * (brier(grid, 0) - brier(r, 0))
    assert abs(grid[np.argmax(exp)] - q) < 1e-3

def test_flat_rho_tilts_optimum_upward():
    # Claim 3: weighting y=0 outcomes by rho<1 makes the optimum q/(q+(1-q)rho) > q
    q, rho = 0.2, 0.5
    grid = np.linspace(0.001, 0.999, 9999)
    exp = q * brier(grid, 1) + (1 - q) * rho * brier(grid, 0)
    assert abs(grid[np.argmax(exp)] - q / (q + (1 - q) * rho)) < 1e-3


# ---------- leave-one-out reference ----------
def test_loo_reference_independent_of_own_report(monkeypatch):
    seen = []
    orig = core.agg_trimmed_capped
    def spy(P, stake, **kw):
        seen.append(P.shape[0]); return orig(P, stake, **kw)
    monkeypatch.setitem(core.AGG, "trimmed", spy)
    p = Params(n_tasks=200, epochs=1, n_ml=10, eta=0.5, n_prov=5)
    run(p, seed=1)
    # routing call uses all 10; each settlement reference uses n_ml - 1
    assert seen[0] == 10 and seen.count(9) == 10

def test_loo_reference_unchanged_when_own_report_changes():
    rng = np.random.default_rng(0)
    P = rng.uniform(0.05, 0.95, (8, 50)); s = np.ones(8)
    ref = agg_trimmed_capped(np.delete(P, 3, 0), np.delete(s, 3))
    P2 = P.copy(); P2[3] = 0.01
    assert np.allclose(ref, agg_trimmed_capped(np.delete(P2, 3, 0), np.delete(s, 3)))


# ---------- trimmed, stake-capped aggregator ----------
def test_trimmed_ignores_extreme_minority():
    P = np.full((10, 1), 0.5); P[0] = 0.99; P[1] = 0.01
    assert abs(agg_trimmed_capped(P, np.ones(10))[0] - 0.5) < 1e-9

def test_trimmed_constant_reports_identity():
    P = np.full((7, 3), 0.2)
    assert np.allclose(agg_trimmed_capped(P, np.ones(7)), 0.2)

def test_stake_cap_neutralises_large_stake():
    P = np.full((5, 1), 0.5); P[0] = 0.01
    big = np.array([100.0, 1, 1, 1, 1])
    assert abs(agg_trimmed_capped(P, big, cap=1.0, trim=0.0)[0] - agg_trimmed_capped(P, np.ones(5), cap=1.0, trim=0.0)[0]) < 1e-12
    assert agg_wmean(P, big)[0] < 0.05  # uncapped mean is captured

def test_trimmed_between_min_and_max():
    rng = np.random.default_rng(3)
    P = rng.uniform(0.01, 0.99, (9, 40)); s = rng.uniform(0.5, 3, 9)
    a = agg_trimmed_capped(P, s)
    assert np.all(a >= P.min(0) - 1e-12) and np.all(a <= P.max(0) + 1e-12)

def test_median_majority_capture():
    P = np.array([[0.9], [0.9], [0.1], [0.1], [0.1]])
    assert agg_median(P, np.ones(5))[0] == pytest.approx(0.1)


# ---------- geometric-decay Sybil math ----------
@pytest.mark.parametrize("others", [0, 1, 2, 4])
@pytest.mark.parametrize("clones", [2, 3, 5])
def test_geometric_decay_makes_cloning_unprofitable(others, clones):
    single = mutant_payout(1 + others, 0, 1.0, "geometric")
    cloned = clones * mutant_payout(clones + others, 0, 1.0, "geometric")
    assert cloned < single

@pytest.mark.parametrize("others", [1, 2, 4])
def test_one_over_n_rewards_cloning(others):
    assert 3 * mutant_payout(3 + others, 0, 1.0, "1/n") > mutant_payout(1 + others, 0, 1.0, "1/n")

def test_geometric_total_payout():
    k = 4
    assert k * mutant_payout(k, 0, 1.0, "geometric") == pytest.approx(1.0 / 2 ** (k - 1))
    assert mutant_payout(0, 0, 1.0, "geometric") == 0.0


# ---------- slashing and self-refutation threshold ----------
def test_invalid_certificates_are_slashed():
    base = Params(n_tasks=300, epochs=3, frac_cheat_prov=0.2, cheat_rate=1.0, mutant_rate=0.0, base_rate=0.0)
    r = run(base, seed=0)
    assert r["burned"] > 0 and r["prov_cheat"] < 0  # no bugs or mutants: cheaters only lose bonds, minus BSAFE pay

def test_cheaters_lose_vs_honest():
    r = run(Params(n_tasks=300, epochs=3, cheat_rate=1.0), seed=0)
    assert r["prov_cheat"] < r["prov_honest"]

@pytest.mark.parametrize("phi,bond,bonus", [(0.5, 0.5, 0.5), (0.5, 1.0, 0.5), (0.5, 2.0, 0.5), (1.0, 5.0, 0.5), (0.8, 3.0, 0.5)])
def test_self_refutation_threshold(phi, bond, bonus):
    r = run(Params(n_tasks=400, epochs=2, sybil_selfref=True, phi=phi, bond=bond, ref_bonus=bonus), seed=2)
    margin = phi * bond + bonus - bond   # profitable iff bond < bonus / (1 - phi)
    if margin > 1e-12: assert r["selfref_profit"] > 0
    elif margin < -1e-12: assert r["selfref_profit"] < 0
    else: assert r["selfref_profit"] == pytest.approx(0.0)

def test_bond_and_window_floor_reduce_suppression_profit():
    b = Params(n_tasks=400, epochs=3, collude_supp=True, agg="median")
    off = run(replace(b, defend_supp=False), seed=0)
    on = run(replace(b, defend_supp=True, W_min=4.0, bond=3.0), seed=0)
    assert on["coll_excess_per_task"] < off["coll_excess_per_task"]
    assert on["coll_false_safe_survival"] <= off["coll_false_safe_survival"]


# ---------- seeded smoke test ----------
def test_small_run_deterministic_and_sane():
    p = Params(n_tasks=400, epochs=3, n_ml=10, n_prov=6, eta=0.5)
    a, b = run(p, seed=7), run(p, seed=7)
    assert a.keys() == b.keys()
    for k in a: assert a[k] == b[k] or (np.isnan(a[k]) and np.isnan(b[k]))
    for k in ("recall", "target_recall", "false_safe_survival"): assert 0.0 <= a[k] <= 1.0
    assert a["ml_lazy"] < a["ml_honest"]

@pytest.mark.parametrize("agg", ["median", "trimmed", "wmean", "skill"])
def test_all_aggregators_run(agg):
    r = run(Params(n_tasks=150, epochs=2, n_ml=10, agg=agg), seed=0)
    assert 0.0 <= r["recall"] <= 1.0
