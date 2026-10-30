"""Compile every .sol under a root with the solc version from SmartBugs versions.csv -> runtime bytecode + CFG JSON.
usage: compile_all.py SB_ROOT OUT_DIR [--files list.txt --version-map map.csv]"""
import csv, json, os, subprocess, sys, hashlib, re
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__)); import evmcfg
SOLC_DIR = Path(os.environ.get('SOLC_ARTIFACTS', Path(sys.prefix)/'.solc-select'/'artifacts'))
def solc_bin(v): return SOLC_DIR/f'solc-{v}'/f'solc-{v}'
def compile_src(path, version):
    r = subprocess.run([str(solc_bin(version)), '--combined-json', 'bin-runtime', str(path)], capture_output=True, text=True, timeout=120)
    if r.returncode != 0: return None, r.stderr[-400:]
    j = json.loads(r.stdout); out = {}
    for k, v in j['contracts'].items():
        if v.get('bin-runtime'): out[k.split(':')[-1]] = re.sub(r'__.{36}__', '0'*40, v['bin-runtime'])  # unlinked library placeholder -> zero address
    return out, None
def main_contract(bins):  # largest runtime = contract under test (heuristic, recorded)
    return max(bins.items(), key=lambda kv: len(kv[1])) if bins else (None, None)
if __name__ == '__main__':
    root, outd = Path(sys.argv[1]), Path(sys.argv[2]); outd.mkdir(parents=True, exist_ok=True)
    vers = {r['file']: r['compiled version'] for r in csv.DictReader(open(root/'versions.csv'))}
    rows = []
    for f, v in sorted(vers.items()):
        bins, err = compile_src(root/f, v); name, rt = main_contract(bins or {})
        rec = {'file': f, 'solc': v, 'ok': bool(rt), 'main': name, 'err': err}
        if rt:
            ins = evmcfg.disasm(rt); g = evmcfg.cfg(ins)
            rec.update(runtime_sha256=hashlib.sha256(bytes.fromhex(rt)).hexdigest(), n_ops=len(ins), n_blocks=g['n_blocks'], n_edges=g['n_edges'])
            stem = f.replace('/', '__')[:-4]
            (outd/f'{stem}.bin-runtime').write_text(rt); (outd/f'{stem}.cfg.json').write_text(json.dumps(g))
        rows.append(rec)
    json.dump(rows, open(outd/'index.json', 'w'), indent=1)
    print(f"compiled {sum(r['ok'] for r in rows)}/{len(rows)}")
