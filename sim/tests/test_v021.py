"""v0.2.1/0.2.2: tied safe-claim pay, spot-check AUC closed forms, rho fit helpers."""
import sys, pathlib, numpy as np, pytest
from dataclasses import replace
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "v02"))
from core import Params, run
import spotcheck as sc

BASE = dict(c=0.1, G=0.05, d=0.8, J=1.0)

def _ratio(rule, mr, seeds=range(3)):
    p = replace(Params(n_tasks=600, epochs=4), safe_pay_rule=rule, mutant_rate=mr)
    return np.mean([run(p, s)["lazy_over_honest"] for s in seeds])

def test_default_is_v02_base():
    assert Params().safe_pay_rule == "base" and Params().search_cost == 0.0

def test_tied_pay_lazy_ratio_ordering():
    for mr in (0.3, 0.9):
        b, t, k = _ratio("base", mr), _ratio("tied", mr), _ratio("kill_required", mr)
        assert b > t > k
    assert _ratio("tied", 0.9) < _ratio("tied", 0.3)

def test_tied_pay_identical_without_mutants():
    p = Params(n_tasks=300, epochs=2, mutant_rate=0.0)
    a, b = run(p, 1), run(replace(p, safe_pay_rule="tied"), 1)
    assert a["prov_lazy"] == b["prov_lazy"] and a["prov_honest"] == b["prov_honest"]

@pytest.mark.parametrize("auc", [0.6, 0.75, 0.9, 0.99])
def test_binary_lambda_min_is_1_over_2_1_minus_auc(auc):
    lam = 1 / (2 * (1 - auc))
    # over single-point ROCs with t - f = 2auc - 1, Lambda=(1-f)/(1-t) is minimised at f=0 (designer's best case)
    fs = np.linspace(0, 2 - 2 * auc - 1e-6, 2001)
    L = (1 - fs) / (1 - (fs + 2 * auc - 1))
    assert L.min() == pytest.approx(lam, rel=1e-9) and np.all(np.diff(L) >= -1e-12)
    if auc > 0.5: assert L[-1] > 100 * lam   # unbounded as t -> 1

@pytest.mark.parametrize("s", [0.05, 0.1, 0.3])
@pytest.mark.parametrize("lam", [1.0, 2.5, 10.0])
def test_binary_P_star_and_s_star_are_indifference_points(s, lam):
    c, G, d, J = BASE["c"], BASE["G"], BASE["d"], BASE["J"]
    P = (c + G * lam * (1 - s) / s) / d - J
    D = d * (J + P) - c
    assert s * D == pytest.approx((1 - s) * G * lam)          # unflagged IC binds exactly
    s_star = G * lam / (G * lam + D)
    assert s_star == pytest.approx(s)                          # s*(P*(s)) = s
    auc = 1 - 1 / (2 * lam)
    assert sc.P_min_binary(auc, s, **BASE) == pytest.approx(max(0.0, P))

def test_binormal_P_eps_monotone_in_auc():
    aucs = np.linspace(0.6, 0.97, 30)
    P = [sc.P_min_eps(a, 0.05, 0.1, **BASE) for a in aucs]
    assert all(np.diff(P) > 0)
    assert sc.P_min_eps(0.9, 0.05, 0.1, **BASE) > sc.P_min_binary(0.9, 0.1, **BASE)

def test_P_eps_gives_eps_shirk():
    for a in (0.6, 0.8, 0.9):
        P = sc.P_min_eps(a, 0.05, 0.1, **BASE)
        assert sc.shirk_frac_real(a, s=0.1, P=P, **BASE) == pytest.approx(0.05, abs=1e-9)

def test_sim_matches_closed_form_small_seed():
    for a in (0.7, 0.9):
        closed = sc.shirk_frac_real(a, s=0.1, P=0.0, **BASE)
        mc = np.mean([sc.mc(a, 0.1, 0.0, seed=k, **BASE)[1] for k in range(3)])
        assert mc == pytest.approx(closed, abs=0.05)

def test_rho_fit_wilson_and_step_model():
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rho"))
    data = pathlib.Path("/workspace/research/two-tier-market/data/rho_bnd_runs.csv")
    if not data.exists(): pytest.skip("rho_bnd_runs.csv not available")
    import json, subprocess
    subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve().parents[1] / "rho" / "fit_rho.py"), str(data)], check=True, capture_output=True)
    out = json.load(open(pathlib.Path(__file__).resolve().parents[1] / "rho" / "rho_fit.json"))
    assert out["step_model_agreement"][0] == out["step_model_agreement"][1]
    m3 = out["by_k"]["3"]["miss_as_miss"]
    assert m3[0] == pytest.approx(0.4) and m3[1] == pytest.approx(0.1176, abs=1e-3)
