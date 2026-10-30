"""Build labelled (original, mutant) pairs: mutate -> compile -> dedupe by runtime hash -> family split.
usage: build_dataset.py SB_ROOT OUT_DIR --seed 1337"""
import argparse, csv, json, hashlib, os, sys, random
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
import mutate, compile_all, evmcfg
ap = argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('out'); ap.add_argument('--seed', type=int, default=1337); ap.add_argument('--order2', type=int, default=8)
a = ap.parse_args(); root, out = Path(a.root), Path(a.out); (out/'src').mkdir(parents=True, exist_ok=True); (out/'bin').mkdir(exist_ok=True)
vers = {r['file']: r['compiled version'] for r in csv.DictReader(open(root/'versions.csv'))}
vulns = {v['path']: sorted({x['category'] for x in v['vulnerabilities']}) for v in json.load(open(root/'vulnerabilities.json'))}
def fam_split(fam):  # frozen: hash of family id, independent of seed and of dataset size
    h = int(hashlib.sha256(fam.encode()).hexdigest(), 16) % 100
    return 'train' if h < 70 else ('val' if h < 85 else 'test')
rows = []; stats = {'sites': 0, 'compile_fail': 0, 'dup_runtime': 0, 'same_as_orig': 0}
for f, v in sorted(vers.items()):
    src = (root/f).read_text(errors='replace'); fam = f
    ob, _ = compile_all.compile_src(root/f, v); oname, ort = compile_all.main_contract(ob)
    ohash = hashlib.sha256(bytes.fromhex(ort)).hexdigest()
    stem = f.replace('/', '__')[:-4]; (out/'bin'/f'{stem}__orig.bin').write_text(ort)
    rows.append(dict(family=fam, variant='orig', split=fam_split(fam), solc=v, main=oname, runtime_sha256=ohash, operators='', injected_class='', sb_labels='|'.join(vulns.get(f, [])), lines='', is_mutant=0))
    seen = {ohash}; seed = (a.seed * 1000003 + int(hashlib.sha256(f.encode()).hexdigest()[:8], 16)) & 0xffffffff
    for mid, chosen in mutate.mutants(src, seed, a.order2):
        stats['sites'] += 1; msrc = mutate.apply(src, chosen); mp = out/'src'/f'{stem}__{mid}.sol'; mp.write_text(msrc)
        mb, err = compile_all.compile_src(mp, v)
        mrt = (mb or {}).get(oname)
        if not mrt: stats['compile_fail'] += 1; mp.unlink(); continue
        h = hashlib.sha256(bytes.fromhex(mrt)).hexdigest()
        if h in seen: stats['same_as_orig' if h == ohash else 'dup_runtime'] += 1; mp.unlink(); continue
        seen.add(h); (out/'bin'/f'{stem}__{mid}.bin').write_text(mrt)
        rows.append(dict(family=fam, variant=mid, split=fam_split(fam), solc=v, main=oname, runtime_sha256=h, operators='+'.join(c[1] for c in chosen),
                         injected_class='|'.join(sorted({c[2] for c in chosen})), sb_labels='|'.join(vulns.get(f, [])), lines='+'.join(str(c[0]+1) for c in chosen), is_mutant=1))
with open(out/'pairs.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
m = [r for r in rows if r['is_mutant']]
summ = dict(seed=a.seed, order2=a.order2, families=len(vers), mutant_pairs=len(m), **stats,
            split_pairs={s: sum(r['split'] == s for r in m) for s in ('train', 'val', 'test')},
            split_families={s: len({r['family'] for r in rows if r['split'] == s}) for s in ('train', 'val', 'test')},
            by_operator={o: sum(r['operators'] == o for r in m) for o in mutate.OPS})
json.dump(summ, open(out/'summary.json', 'w'), indent=1); print(json.dumps(summ, indent=1))
