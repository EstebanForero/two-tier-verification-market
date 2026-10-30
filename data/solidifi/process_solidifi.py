"""Compile SolidiFI buggy contracts -> runtime bytecode (largest contract) into /workspace/data/solidifi/derived.
solc: 0.5.0 when the pragma allows it (to match SmartBugs mutants, which are <=0.5.0), else 0.5.12.
SolidiFI bugs are *injected* into real Etherscan contracts (code-injection, not real bugs)."""
import hashlib, json, os, re, subprocess, sys, pathlib
D = pathlib.Path(os.environ.get('SOLIDIFI_DIR', '/workspace/data/solidifi')); O = D / 'derived'; (O / 'bin').mkdir(parents=True, exist_ok=True)
A = pathlib.Path(sys.prefix) / '.solc-select/artifacts'
CLS = {'Overflow-Underflow': 'arithmetic', 'Re-entrancy': 'reentrancy', 'tx.origin': 'access_control', 'Unchecked-Send': 'unchecked_low_level_calls',
       'Unhandled-Exceptions': 'unchecked_low_level_calls', 'TOD': 'front_running', 'Timestamp-Dependency': 'time_manipulation'}
def pick(src):
    p = re.search(r'pragma solidity ([^;]*);', src); p = p.group(1) if p else ''
    return '0.5.0' if re.fullmatch(r'\^0\.5\.0|>=0\.4\.\d+ <0\.6\.0|>=0\.5\.0', p.strip()) else '0.5.12'
recs, seen = [], set()
for f in sorted((D / 'buggy_contracts').rglob('*.sol')):
    v = pick(f.read_text(errors='ignore')); s = A / f'solc-{v}' / f'solc-{v}'
    r = subprocess.run([str(s), '--combined-json', 'bin-runtime', str(f)], capture_output=True, text=True)
    best = ''
    try:
        for k, c in json.loads(r.stdout)['contracts'].items():
            if len(c['bin-runtime']) > len(best): best = c['bin-runtime']
    except Exception: pass
    rec = dict(file=str(f.relative_to(D)), cls=CLS.get(f.parent.name, f.parent.name), solc=v, ok=bool(best))
    if best:
        best = re.sub(r'__\S{36}__|__\$[0-9a-f]{34}\$__', '0' * 40, best); h = hashlib.sha256(best.encode()).hexdigest()
        rec.update(sha=h, dup=h in seen); seen.add(h)
        if not rec['dup']: (O / 'bin' / (h[:16] + '.bin')).write_text(best)
    recs.append(rec)
json.dump(recs, open(O / 'solidifi.json', 'w'), indent=0)
ok = [r for r in recs if r['ok'] and not r['dup']]
print(dict(total=len(recs), ok=sum(r['ok'] for r in recs), unique=len(ok), solc_050=sum(r['solc'] == '0.5.0' for r in ok)))
