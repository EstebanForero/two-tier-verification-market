"""v0.3: depth-dependent rho_bnd."""
import sys, pathlib, json, numpy as np, pytest
from dataclasses import replace
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "v02"))
import depth as D
from core import Params, run

def test_flat_mode_is_default_and_reproduces_v02_json():
    assert Params().rho_mode == "flat"
    ref = json.load(open(pathlib.Path(__file__).resolve().parents[1] / "v02" / "results_v02.json"))
    # E2 row at rho=0.71: recompute 3 seeds and compare to per-seed runs of an explicitly flat config
    p = replace(Params(), frac_adv=0.0, frac_lazy=0.2, frac_infl=0.2, eta=0.3, rho_bnd=0.71)
    a = [run(p, s)["ml_infl"] for s in range(3)]
    b = [run(replace(p, rho_mode="flat", bound_k=1, depth_dist=D.Geometric(0.99)), s)["ml_infl"] for s in range(3)]
    assert a == b                                   # depth params ignored in flat mode, bit-identical
    assert any(r.get("rho_bnd") == 0.71 for r in ref["E2_rho"])

def test_flat_mode_exact_values():
    o = run(Params(n_tasks=300, epochs=2), 0)
    assert o["rho_safe"] == 0.71

@pytest.mark.parametrize("dist", [D.Geometric(0.3), D.Geometric(0.8), D.DiscretePareto(0.7)])
def test_rho_rises_with_k_without_timeouts(dist):
    r = [D.rho_bayes(0.3, k, dist) for k in range(1, 12)]
    assert all(np.diff(r) > 0) and r[-1] < 1

def test_deep_bugs_lower_rho():
    for k in (2, 4, 6):
        assert D.rho_bayes(0.3, k, D.Geometric(0.8)) < D.rho_bayes(0.3, k, D.Geometric(0.3))
    shallow = D.Empirical([1, 2, 2, 3]); deep = D.Empirical([1, 2, 2, 3, 10, 12])
    assert D.rho_bayes(0.3, 4, shallow) == pytest.approx(1.0)
    assert D.rho_bayes(0.3, 4, deep) < 1.0

def test_timeout_lowers_rho_and_detection():
    g = D.Geometric(0.5)
    assert D.rho_bayes(0.3, 8, g, D.step_timeout(6)) == pytest.approx(0.7)   # no run finishes -> rho = 1 - pi
    p = replace(Params(n_tasks=400, epochs=2), rho_mode="depth", detect=1.0, depth_dist=g)
    assert run(replace(p, bound_k=8, p_complete=D.step_timeout(6)), 0)["recall"] < run(replace(p, bound_k=6), 0)["recall"]

def test_rho_formula_closed_form():
    assert D.rho_bayes(0.1, 3, D.Geometric(0.5)) == pytest.approx(0.9 / (0.9 + 0.1 * 0.125))

@pytest.mark.parametrize("dist", [D.Geometric(0.6), D.DiscretePareto(0.8)])
def test_sampler_matches_sf(dist):
    x = dist.sample(np.random.default_rng(0), 200000)
    for k in (1, 2, 4, 8):
        assert np.mean(x > k) == pytest.approx(dist.sf(k), abs=0.005)

def test_empirical_loader_fixture(tmp_path):
    f = tmp_path / "depths.csv"
    f.write_text("Mutant_ID,Ground_Truth_Buggy,Bug_Min_Depth,Count\nm1,1,1,2\nm2,1,3,1\nm3,1,>8,1\nm4,0,,5\nm5,true,inf,0\n")
    e = D.load_depth_csv(f)
    assert e.sf(0) == 1.0 and e.sf(1) == pytest.approx(0.5) and e.sf(3) == pytest.approx(0.25) and e.sf(100) == pytest.approx(0.25)
    g = tmp_path / "plain.csv"; g.write_text("depth\n2\n4\n")
    assert D.load_depth_csv(g).sf(3) == pytest.approx(0.5)
    bad = tmp_path / "bad.csv"; bad.write_text("foo\n1\n")
    with pytest.raises(ValueError): D.load_depth_csv(bad)
    p = replace(Params(n_tasks=300, epochs=2), rho_mode="depth", depth_dist=e, bound_k=3)
    assert run(p, 0)["rho_safe"] == pytest.approx(D.rho_bayes(0.1, 3, e, detect=0.8))
