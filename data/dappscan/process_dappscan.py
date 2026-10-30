"""DAppSCAN-Bytecode -> real-bug set (positive-only labels) for the mutant-vs-real gate and real-only calibration.
Data has NO license: inputs and outputs live OUTSIDE the repo (default /workspace/data/dappscan). Nothing here is committed but code.
Steps: filter SWC {101,104,105,107,112,113,114,115,128}; take each labelled contract's runtime bytecode; record solc version;
dedup by runtime hash; frozen split by DApp (hash of DApp id); map label -> function via AST FunctionDefinition src range,
then -> runtime PCs via srcmap-runtime (instructions whose source range lies inside the function).
usage: process_dappscan.py [DAPPSCAN_REPO] [OUT_DIR]"""
import json, glob, os, sys, hashlib, csv, ast as pyast, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts')); import evmcfg
REPO = sys.argv[1] if len(sys.argv) > 1 else '/workspace/data/dappscan/repo'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/workspace/data/dappscan/derived'
KEEP = {'101', '104', '105', '107', '112', '113', '114', '115', '128'}
os.makedirs(OUT + '/bin', exist_ok=True)
def split_of(dapp):
    h = int(hashlib.sha256(dapp.encode()).hexdigest(), 16) % 100
    return 'train' if h < 70 else ('val' if h < 85 else 'test')
def parse_srcmap(sm):
    out = []; s = l = f = 0; j = '-'
    for e in sm.split(';'):
        p = e.split(':')
        if len(p) > 0 and p[0] != '': s = int(p[0])
        if len(p) > 1 and p[1] != '': l = int(p[1])
        if len(p) > 2 and p[2] != '': f = int(p[2])
        out.append((s, l, f))
    return out
def func_ranges(src_entry):
    try: a = src_entry if isinstance(src_entry, dict) else pyast.literal_eval(src_entry)
    except Exception: return {}
    res = {}
    def walk(n):
        if isinstance(n, dict):
            if n.get('nodeType') == 'FunctionDefinition' or n.get('name') == 'FunctionDefinition':
                nm = n.get('name') if n.get('nodeType') else (n.get('attributes') or {}).get('name')
                st, ln, fi = map(int, n['src'].split(':')); res.setdefault(nm or '', []).append((st, ln, fi))
            for v in n.values(): walk(v)
        elif isinstance(n, list):
            for v in n: walk(v)
    walk(a.get('AST', a)); return res
rows = []; seen = {}; stats = dict(labels_total=0, labels_kept=0, no_bytecode=0, empty_runtime=0, dup_hash=0, fn_mapped=0)
for lf in sorted(glob.glob(f'{REPO}/DAppSCAN-bytecode/SWCbytecode/*/*.json')):
    dapp = lf.split('/')[-2]; node = os.path.basename(lf); labs = json.load(open(lf))['SWCs']
    stats['labels_total'] += len(labs)
    labs = [x for x in labs if re.match(r'SWC-(\d+)', x['category']).group(1) in KEEP]
    if not labs: continue
    stats['labels_kept'] += len(labs)
    bf = f'{REPO}/DAppSCAN-bytecode/bytecode/{dapp}/{node}'
    if not os.path.exists(bf): stats['no_bytecode'] += 1; continue
    d = json.load(open(bf)); cname = node[:-5]
    key = next((k for k in d['contracts'] if k.split(':')[-1] == cname), None)
    c = d['contracts'].get(key, {}); rt = c.get('bin-runtime', '')
    rt = re.sub(r'__.{36}__', '0' * 40, rt)
    if not rt: stats['empty_runtime'] += 1; continue
    h = hashlib.sha256(bytes.fromhex(rt)).hexdigest()
    if h in seen: stats['dup_hash'] += 1; seen[h]['dup_of'].append(f'{dapp}/{node}'); continue
    ins = evmcfg.disasm(rt); sm = parse_srcmap(c.get('srcmap-runtime', ''))
    srcfile = key.rsplit(':', 1)[0]; fidx = d['sourceList'].index(srcfile) if srcfile in d.get('sourceList', []) else None
    fr = {}
    for sf, ent in d.get('sources', {}).items():  # functions may be inherited from other files
        for nm, rs in func_ranges(ent).items(): fr.setdefault(nm, []).extend(rs)
    lab_out = []
    for x in labs:
        fn = x['function']; pcs = []
        for (st, ln, fi) in fr.get(fn, []):
            pcs += [ins[i][0] for i, (s, l, f) in enumerate(sm[:len(ins)]) if f == fi and st <= s and s + l <= st + ln]
        if pcs: stats['fn_mapped'] += 1
        lab_out.append(dict(swc=x['category'][:7], function=fn, lines=x['lines'], n_pcs=len(pcs), pc_min=min(pcs) if pcs else None, pc_max=max(pcs) if pcs else None))
    open(f'{OUT}/bin/{h[:16]}.bin', 'w').write(rt)
    rec = dict(dapp=dapp, contract=cname, solc=d.get('version', '').split('+')[0], runtime_sha256=h, split=split_of(dapp),
               swcs='|'.join(sorted({l['swc'] for l in lab_out})), labels=lab_out, n_ops=len(ins), dup_of=[])
    seen[h] = rec; rows.append(rec)
json.dump(rows, open(f'{OUT}/real_bugs.json', 'w'), indent=0)
summ = dict(stats, contracts=len(rows), dapps=len({r['dapp'] for r in rows}),
            split_contracts={s: sum(r['split'] == s for r in rows) for s in ('train', 'val', 'test')},
            solc_ge_0_6=sum(r['solc'] >= '0.6' for r in rows))
json.dump(summ, open(f'{OUT}/summary.json', 'w'), indent=1); print(json.dumps(summ, indent=1))
