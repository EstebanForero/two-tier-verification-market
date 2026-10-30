"""FV kill filter: a mutant is 'killed' if halmos finds an input on which original and mutant runtime bytecode
behave differently (success flag, returndata, ETH balance, or storage slots 0-7) from empty storage, one call.
Usage: python kill.py [solver_timeout_s] [worker/nworkers]; per-family wall cap KILL_FAMILY_CAP_S (240). Writes results/kill_<w>.csv; build dirs proj<w>/ (gitignored)."""
import csv, json, os, re, shutil, subprocess, sys, time, pathlib
R = pathlib.Path(__file__).resolve().parents[2]; DS = R / 'data/build/ds'
TO = int(sys.argv[1]) if len(sys.argv) > 1 else 20; W, NW = (int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else '0/1').split('/'))
CAP = int(os.environ.get('KILL_FAMILY_CAP_S', 240)); LIM = 10**9
OUT = pathlib.Path(__file__).parent / f'results/kill_{W}.csv'; P = pathlib.Path(__file__).parent / f'proj{W}'; OUT.parent.mkdir(exist_ok=True)
(P / 'test').mkdir(parents=True, exist_ok=True)
if not (P / 'lib').exists(): os.symlink(R / 'fv/halmos/lib', P / 'lib')
shutil.copy(R / 'fv/halmos/foundry.toml', P / 'foundry.toml')
rows = list(csv.DictReader(open(DS / 'pairs.csv'))); fams = {}
for r in rows: fams.setdefault(r['family'], []).append(r)
def binf(r): return DS / 'bin' / (r['family'].replace('/', '__').removesuffix('.sol') + '__' + r['variant'] + '.bin')
done = {(d['family'], d['variant']) for f in OUT.parent.glob('kill_*.csv') for d in csv.DictReader(open(f))}
out = list(csv.DictReader(open(OUT))) if OUT.exists() else []
HDR = '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import "forge-std/Test.sol";
contract K is Test {
  address constant A = address(0xA0000); address constant B = address(0xB0000);
  function d(bytes memory o, bytes memory m, bytes4 s, bytes32 x, bytes32 y, address c, uint96 v) internal {
    vm.assume(c != A && c != B && c != address(this));
    vm.etch(A, o); vm.etch(B, m); vm.deal(c, uint(v) * 2);
    bytes memory data = abi.encodePacked(s, x, y);
    vm.prank(c); (bool s1, bytes memory r1) = A.call{value: v}(data);
    vm.prank(c); (bool s2, bytes memory r2) = B.call{value: v}(data);
    assert(s1 == s2); assert(keccak256(r1) == keccak256(r2)); assert(A.balance == B.balance);
    for (uint i = 0; i < 8; i++) assert(vm.load(A, bytes32(i)) == vm.load(B, bytes32(i)));
  }
'''
for n, (fam, rs) in enumerate(fams.items()):
    if n % NW != W: continue
    orig = [r for r in rs if r['variant'] == 'orig'][0]; ob = binf(orig).read_text().strip()
    ms = [r for r in rs if r['is_mutant'] == '1' and (fam, r['variant']) not in done and binf(r).exists()]
    if not ms: continue
    body = HDR + ''.join(f'  function check_{r["variant"]}(bytes4 s, bytes32 x, bytes32 y, address c, uint96 v) public {{ d(hex"{ob}", hex"{binf(r).read_text().strip()}", s, x, y, c, v); }}\n' for r in ms) + '}\n'
    for f in (P / 'test').glob('*.sol'): f.unlink()
    (P / 'test/K.t.sol').write_text(body); js = f'/tmp/kill{W}.json'; t0 = time.time()
    try:
        subprocess.run(['halmos', '--solver-timeout-assertion', f'{TO}s', '--json-output', js, '--loop', '4'], cwd=P,
                       capture_output=True, text=True, timeout=min(TO * len(ms) * 2 + 120, CAP))
        res = {t['name'].split('(')[0].removeprefix('check_'): t for ts in json.load(open(js))['test_results'].values() for t in ts}
    except Exception as e: res = {}
    for r in ms:
        t = res.get(r['variant'])
        v = 'error' if t is None else ('equiv_bounded' if t['exitcode'] == 0 else ('killed' if t.get('models') else 'timeout'))
        out.append(dict(family=fam, variant=r['variant'], split=r['split'], operators=r['operators'], verdict=v,
                        time_s=round(t['time'][0], 2) if t and isinstance(t.get('time'), list) else '', solver_timeout_s=TO))
    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print(fam, len(ms), round(time.time() - t0, 1), flush=True)
