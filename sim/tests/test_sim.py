import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import sim

def test_run_returns_valid_recall():
    r = sim.run(n_tasks=200, epochs=2, seed=0)
    assert 0.0 <= r["recall"] <= 1.0
    assert 0.0 <= r["target_recall"] <= 1.0
