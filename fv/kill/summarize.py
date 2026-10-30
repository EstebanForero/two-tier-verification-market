"""Merge results/kill_*.csv -> results/kill.csv, print verdict counts overall / by split / by operator, and write
data/build/ds/pairs_killed.csv (pairs.csv rows of originals + killed mutants only; regenerable, gitignored)."""
import csv, glob, collections, json, pathlib
H = pathlib.Path(__file__).parent; R = H.parents[1]
rows = [r for f in sorted(glob.glob(str(H / 'results/kill_*.csv'))) for r in csv.DictReader(open(f))]
with open(H / 'results/kill.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(sorted(rows, key=lambda r: (r['family'], r['variant'])))
C = collections.Counter
s = dict(n=len(rows), verdict=C(r['verdict'] for r in rows),
         by_split={sp: C(r['verdict'] for r in rows if r['split'] == sp) for sp in ('train', 'val', 'test')},
         by_operator_first_order={op: C(r['verdict'] for r in rows if r['operators'] == op) for op in sorted({r['operators'] for r in rows if '+' not in r['operators']})},
         families=len({r['family'] for r in rows}))
killed = {(r['family'], r['variant']) for r in rows if r['verdict'] == 'killed'}
P = list(csv.DictReader(open(R / 'data/build/ds/pairs.csv')))
keep = [p for p in P if p['is_mutant'] == '0' or (p['family'], p['variant']) in killed]
with open(R / 'data/build/ds/pairs_killed.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(P[0])); w.writeheader(); w.writerows(keep)
s['killed_pairs_by_split'] = C(p['split'] for p in keep if p['is_mutant'] == '1')
json.dump(s, open(H / 'results/kill_summary.json', 'w'), indent=1); print(json.dumps(s, indent=1))
