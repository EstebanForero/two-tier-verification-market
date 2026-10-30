"""Per-mutant bug depth from the depth sweep (depth.py) -> CSVs in the rho_depth.md empirical schema.
first_cex_k = smallest k with a counterexample (diff: killed; sec: sec_killed); blank if none was found or the run timed out.
Writes OUTDIR/bug_depth.csv (diff = non-equivalence mode), OUTDIR/bug_depth_sec.csv (security-property mode), each with
columns mutant_id, family, operator, first_cex_k, max_k_tried; status/kill_mode go to OUTDIR/bug_depth_status.csv.
usage: python export_depth.py DS OUTDIR"""
import csv, sys, pathlib, collections, json
RES = pathlib.Path(__file__).parent / 'results'; DS, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
muts = [r for r in csv.DictReader(open(DS / 'pairs.csv')) if r['is_mutant'] == '1']
def rows(tag): return {f"{d['family']}|{d['variant']}": d for f in RES.glob(f'{tag}_*.csv') for d in csv.DictReader(open(f))}
status_rows = []; hist = {}
for mode, kill in (('diff', 'killed'), ('sec', 'sec_killed')):
    per_k = {}
    for k in range(1, 7):
        t = rows(f'depth_{mode}_k{k}')
        if mode == 'diff' and k == 1: t = {**rows('kill'), **t, **{i: d for i, d in rows('depth_diff_k1retry').items() if d['verdict'] != 'error' or i not in t}}
        if t: per_k[k] = t
    out = []
    for m in muts:
        i = f"{m['family']}|{m['variant']}"; mk, first, last, ts = 0, '', '', ''
        for k in sorted(per_k):
            d = per_k[k].get(i)
            if d is None: continue
            mk, last = k, d['verdict']
            if d['verdict'] == kill: first, ts = k, d['time_s']; break
        st = 'killed' if first else {'equiv_bounded': 'safe_to_max', 'prop_holds': 'safe_to_max', 'timeout': 'timeout', '': 'not_run'}.get(last, 'orig_violates' if last.startswith('violated_orig') else 'error')
        mid = f"{m['family'].removeprefix('dataset/').removesuffix('.sol')}::{m['variant']}"
        out.append(dict(mutant_id=mid, family=m['family'], operator=m['operators'], first_cex_k=first, max_k_tried=mk))
        status_rows.append(dict(mutant_id=mid, kill_mode=mode, status=st, last_verdict=last, time_s_at_first_cex=ts))
    with open(OUT / ('bug_depth.csv' if mode == 'diff' else 'bug_depth_sec.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    srs = [s for s in status_rows if s['kill_mode'] == mode]
    hist[mode] = dict(n=len(out), first_cex_k=dict(sorted(collections.Counter(r['first_cex_k'] for r in out if r['first_cex_k']).items())),
                      status=dict(collections.Counter(s['status'] for s in srs)), max_k_tried=dict(sorted(collections.Counter(r['max_k_tried'] for r in out).items())))
with open(OUT / 'bug_depth_status.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(status_rows[0])); w.writeheader(); w.writerows(status_rows)
json.dump(hist, open(OUT / 'bug_depth_summary.json', 'w'), indent=1); print(json.dumps(hist, indent=1))
