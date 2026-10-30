"""Depth-bounded Halmos sweep for rho_bnd + counterexample replay with forge (revm).
For each target T and k in K: halmos --match-contract T_<T> --match-test check_seq_k<k>; verdict safe/cex/timeout/error;
each cex is replayed concretely in a generated forge test (cex_replayed = forge reports the same assertion failure).
usage: python fv/run_rho.py OUT.csv [timeout_s]"""
import os, subprocess, json, csv, sys, time, os, re
from pathlib import Path
HP = Path(__file__).parent / 'halmos'; OUT = sys.argv[1]; TO = int(sys.argv[2]) if len(sys.argv) > 2 else 60
K = [1, 2, 3, 4, 6, 8]
# target: (smartbugs family, mutant_id, bug_class, ground_truth_buggy, min_depth_of_bug or None)
T = {'SWalletV': ('access_control/wallet_02_refund_nosub.sol', 'orig', 'access_control', 1, 3),
     'SWalletF': ('access_control/wallet_02_refund_nosub.sol', 'fix', 'access_control', 0, None),
     'SMultiV': ('arithmetic/integer_overflow_multitx_multifunc_feasible.sol', 'orig', 'arithmetic', 1, 2),
     'SMultiF': ('arithmetic/integer_overflow_multitx_multifunc_feasible.sol', 'fix', 'arithmetic', 0, None),
     'GateF': ('synthetic/gate', 'fix', 'access_control', 0, None),
     'GateM3': ('synthetic/gate', 'GATE_3', 'access_control', 1, 3),
     'GateM6': ('synthetic/gate', 'GATE_6', 'access_control', 1, 6),
     'GateM10': ('synthetic/gate', 'GATE_10', 'access_control', 1, 10)}
env = dict(os.environ, PATH=os.path.expanduser('~/.foundry/bin') + ':' + os.environ['PATH'])
def replay(tgt, k, model):
    ops = 0; xs = ['0'] * 12
    for v in model.values():
        n = v['variable_name']
        if n == 'ops': ops = int(v['value'])
        m = re.match(r'xs\[(\d+)\]', n)
        if m: xs[int(m.group(1))] = str(int(v['value']))
    name = f'R_{tgt}_k{k}'; f = HP / 'test' / f'{name}.t.sol'
    f.write_text(f'// SPDX-License-Identifier: MIT\npragma solidity ^0.8.24;\nimport "./Seq.t.sol";\n'
                 f'contract {name} is T_{tgt} {{ function test_replay() public {{ uint[12] memory xs = [uint({xs[0]}),{",".join(xs[1:])}]; run({ops}, xs, {k}); }} }}\n')
    t0 = time.time(); r = subprocess.run(['forge', 'test', '--match-contract', name], cwd=HP, capture_output=True, text=True, env=env, timeout=300)
    f.unlink(); out = r.stdout + r.stderr
    return ('[FAIL' in out and 'test_replay' in out), round(time.time() - t0, 2)
rows = list(csv.DictReader(open(OUT))) if os.path.exists(OUT) else []  # resume
done = {(r['target'], int(r['bound_k'])) for r in rows}
for tgt, (fam, mid, cls, gt, dmin) in T.items():
    for k in K:
        if (tgt, k) in done: continue
        if any(r['target'] == tgt and r['verdict'] == 'timeout' and int(r['bound_k']) < k for r in rows): continue  # deeper k cannot be cheaper; skip
        js = f'/tmp/h_{tgt}_{k}.json'; t0 = time.time()
        try:
            r = subprocess.run(['halmos', '--match-contract', f'^T_{tgt}$', '--match-test', f'^check_seq_k{k}\\(', '--loop', '16',
                                '--solver-timeout-assertion', f'{TO}s', '--json-output', js], cwd=HP, capture_output=True, text=True, env=env, timeout=TO * 4 + 60)
            res = json.load(open(js))['test_results']; tr = next(iter(res.values()))[0]
            verdict = {0: 'safe', 1: 'cex'}.get(tr['exitcode'], 'error')
            if tr['exitcode'] == 1 and not tr.get('models'): verdict = 'timeout' if 'TIMEOUT' in r.stdout else 'error'
            models = [m['model'] for m in (tr.get('models') or []) if m.get('is_valid', True)]
        except subprocess.TimeoutExpired: verdict, models = 'timeout', []
        except Exception as e: verdict, models = 'error', []
        dt = round(time.time() - t0, 2); rep, rt = ('', '')
        if verdict == 'cex' and models:
            rep, rt = replay(tgt, k, models[0]); json.dump(models[0], open(f'{OUT}.cex_{tgt}_k{k}.json', 'w'))
        rows.append(dict(contract=fam, target=tgt, mutant_id=mid, bug_class=cls, tool='halmos-0.3.3', bound_k=k, timeout_s=TO, verdict=verdict,
                         time_s=dt, ground_truth_buggy=gt, gt_source='smartbugs-label' if mid == 'orig' else ('injected' if gt else 'manual-fix'),
                         bug_min_depth=dmin or '', cex_replayed=rep, replay_time_s=rt))
        print(rows[-1], flush=True)
        with open(OUT, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
