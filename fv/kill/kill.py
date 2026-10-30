"""FV kill filter: a mutant is 'killed' if halmos finds an input on which original and mutant runtime bytecode
behave differently (success flag, returndata, ETH balance, or storage slots 0-7) from empty storage, one call.
Usage: python kill.py [solver_timeout_s] [worker/nworkers]; per-family wall cap KILL_FAMILY_CAP_S (240). Writes results/kill_<w>.csv; build dirs proj<w>/ (gitignored).
Env: KILL_DS dataset dir (default data/build/ds); KILL_TAG output prefix (default 'kill');
KILL_RETRY=1 re-runs only rows whose earliest verdict was timeout/error (output <TAG>_<w>.csv, skip set = rows in <TAG>_*.csv);
KILL_MODE=sec: security-property kill instead of differential. With 1 ETH preloaded and empty storage, after one symbolic call from
an arbitrary caller: (P1) contract balance not below 1 ETH (no drain beyond caller's own deposit), (P2) code still present (no selfdestruct).
A mutant is sec-killed iff the original passes check_orig (no cex within bounds) and the mutant has a cex."""
import csv, json, os, re, shutil, subprocess, sys, time, pathlib
R = pathlib.Path(__file__).resolve().parents[2]; DS = pathlib.Path(os.environ.get('KILL_DS', R / 'data/build/ds')).resolve()
TAG = os.environ.get('KILL_TAG', 'kill'); RETRY = os.environ.get('KILL_RETRY') == '1'; SEC = os.environ.get('KILL_MODE') == 'sec'; K = int(os.environ.get('KILL_K', 1))  # K = number of sequential symbolic calls (bug depth)
ONLY = set(open(os.environ['KILL_ONLY']).read().split()) if os.environ.get('KILL_ONLY') else None  # optional 'family|variant' allow-list
TO = int(sys.argv[1]) if len(sys.argv) > 1 else 20; W, NW = (int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else '0/1').split('/'))
CAP = int(os.environ.get('KILL_FAMILY_CAP_S', 240)); LIM = 10**9
OUT = pathlib.Path(__file__).parent / f'results/{TAG}_{W}.csv'; P = pathlib.Path(__file__).parent / f'proj{TAG}{W}'; OUT.parent.mkdir(exist_ok=True)
(P / 'test').mkdir(parents=True, exist_ok=True)
if not (P / 'lib').exists(): os.symlink(R / 'fv/halmos/lib', P / 'lib')
shutil.copy(R / 'fv/halmos/foundry.toml', P / 'foundry.toml')
rows = list(csv.DictReader(open(DS / 'pairs.csv'))); fams = {}
for r in rows: fams.setdefault(r['family'], []).append(r)
def binf(r): return DS / 'bin' / (r['family'].replace('/', '__').removesuffix('.sol') + '__' + r['variant'] + '.bin')
done = {(d['family'], d['variant']) for f in OUT.parent.glob(f'{TAG}_*.csv') for d in csv.DictReader(open(f))}
if RETRY:  # only retry rows that earlier first-pass runs left undecided
    prev = {(d['family'], d['variant']): d['verdict'] for f in OUT.parent.glob('kill_*.csv') for d in csv.DictReader(open(f))}
    done |= {k for k, v in prev.items() if v not in ('timeout', 'error')} | ({(r['family'], r['variant']) for r in rows} - set(prev))
out = list(csv.DictReader(open(OUT))) if OUT.exists() else []
def harness(k, sec):
    ps = ', '.join(f'bytes4 s{i}, bytes32 x{i}, bytes32 y{i}, address c{i}, uint96 v{i}' for i in range(k))
    args = ', '.join(f's{i}, x{i}, y{i}, c{i}, v{i}' for i in range(k))
    h = 'pragma solidity ^0.8.24;\nimport "forge-std/Test.sol";\ncontract K is Test {\n  address constant A = address(0xA0000); address constant B = address(0xB0000);\n'
    if sec:
        h += f'  function p(bytes memory code, {ps}) internal {{\n    vm.etch(A, code); vm.deal(A, 1 ether);\n'
        for i in range(k): h += f'    vm.assume(c{i} != A && c{i} != address(this)); vm.deal(c{i}, uint(v{i}) * 2); vm.prank(c{i}); A.call{{value: v{i}}}(abi.encodePacked(s{i}, x{i}, y{i}));\n'
        h += '    assert(A.balance >= 1 ether); assert(A.code.length > 0);\n  }\n'
    else:
        h += f'  function d(bytes memory o, bytes memory m, {ps}) internal {{\n    vm.etch(A, o); vm.etch(B, m); bool s1; bool s2; bytes memory r1; bytes memory r2;\n'
        for i in range(k): h += (f'    vm.assume(c{i} != A && c{i} != B && c{i} != address(this)); vm.deal(c{i}, uint(v{i}) * 2);\n'
            f'    vm.prank(c{i}); (s1, r1) = A.call{{value: v{i}}}(abi.encodePacked(s{i}, x{i}, y{i}));\n'
            f'    vm.prank(c{i}); (s2, r2) = B.call{{value: v{i}}}(abi.encodePacked(s{i}, x{i}, y{i}));\n'
            '    assert(s1 == s2); assert(keccak256(r1) == keccak256(r2));\n')
        h += '    assert(A.balance == B.balance);\n    for (uint i = 0; i < 8; i++) assert(vm.load(A, bytes32(i)) == vm.load(B, bytes32(i)));\n  }\n'
    return '// SPDX-License-Identifier: MIT\n' + h, ps, args
HDR, PS, ARGS = harness(K, SEC)
for n, (fam, rs) in enumerate(fams.items()):
    if n % NW != W: continue
    orig = [r for r in rs if r['variant'] == 'orig'][0]; ob = binf(orig).read_text().strip()
    ms = [r for r in rs if r['is_mutant'] == '1' and (fam, r['variant']) not in done and binf(r).exists() and (ONLY is None or f'{fam}|{r["variant"]}' in ONLY)]
    if not ms: continue
    if SEC: body = HDR + f'  function check_orig({PS}) public {{ p(hex"{ob}", {ARGS}); }}\n' + ''.join(f'  function check_{r["variant"]}({PS}) public {{ p(hex"{binf(r).read_text().strip()}", {ARGS}); }}\n' for r in ms) + '}\n'
    else: body = HDR + ''.join(f'  function check_{r["variant"]}({PS}) public {{ d(hex"{ob}", hex"{binf(r).read_text().strip()}", {ARGS}); }}\n' for r in ms) + '}\n'
    for f in (P / 'test').glob('*.sol'): f.unlink()
    (P / 'test/K.t.sol').write_text(body); js = f'/tmp/{TAG}{W}.json'; t0 = time.time()
    try:
        subprocess.run(['halmos', '--solver-timeout-assertion', f'{TO}s', '--json-output', js, '--loop', '4'], cwd=P,
                       capture_output=True, text=True, timeout=min(TO * (len(ms) + SEC) * 2 + 120, CAP))
        res = {t['name'].split('(')[0].removeprefix('check_'): t for ts in json.load(open(js))['test_results'].values() for t in ts}
    except Exception as e: res = {}
    vd = lambda t: 'error' if t is None else 'stuck_unsupported' if str(t['exitcode']) == '3' else ('equiv_bounded' if t['exitcode'] == 0 else ('killed' if t.get('models') else 'timeout'))
    ov = vd(res.get('orig')) if SEC else ''
    for r in ms:
        t = res.get(r['variant']); v = vd(t)
        if SEC:  # rename: holds / violated; a violation only counts as a sec-kill if the original holds
            v = {'equiv_bounded': 'prop_holds', 'timeout': 'timeout', 'error': 'error', 'stuck_unsupported': 'stuck_unsupported'}.get(v) or ('sec_killed' if ov == 'equiv_bounded' else f'violated_orig_{ov}')
        out.append(dict(family=fam, variant=r['variant'], split=r['split'], operators=r['operators'], verdict=v,
                        time_s=round(t['time'][0], 2) if t and isinstance(t.get('time'), list) else '', solver_timeout_s=TO, cap_s=CAP, k=K, orig_verdict=ov))
    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print(fam, len(ms), round(time.time() - t0, 1), flush=True)
