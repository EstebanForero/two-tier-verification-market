"""Bug-depth sweep driver: for each kill mode (diff = non-equivalence, sec = security property) run kill.py at
k = 1..KMAX sequential symbolic calls, each k only on mutants not yet killed in that mode; stop launching new k after DEADLINE.
k=1 diff reuses first-pass results (results/kill_*.csv) for mutation ids already checked, then retries their timeout/error rows
with a longer cap. usage: python depth.py MODE KMAX DEADLINE_EPOCH NWORKERS (env KILL_DS must point to the dataset)"""
import csv, os, subprocess, sys, time, pathlib
H = pathlib.Path(__file__).parent; RES = H / 'results'
MODE, KMAX, DL, NW = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
DS = pathlib.Path(os.environ['KILL_DS']); muts = [r for r in csv.DictReader(open(DS / 'pairs.csv')) if r['is_mutant'] == '1']
key = lambda r: f"{r['family']}|{r['variant']}"
def rows(tag): return {key(d): d for f in RES.glob(f'{tag}_*.csv') for d in csv.DictReader(open(f))}
def run(tag, ids, to, cap, k):
    if not ids or time.time() > DL: return False
    lst = RES / f'{tag}.only'; lst.write_text('\n'.join(ids))
    env = dict(os.environ, KILL_TAG=tag, KILL_K=str(k), KILL_ONLY=str(lst), KILL_FAMILY_CAP_S=str(cap), **({'KILL_MODE': 'sec'} if MODE == 'sec' else {}))
    ps = [subprocess.Popen([sys.executable, str(H / 'kill.py'), str(to), f'{w}/{NW}'], env=env, stdout=open(RES / f'{tag}_{w}.log', 'a'), stderr=subprocess.STDOUT) for w in range(NW)]
    for p in ps: p.wait()
    return True
KILL = 'killed' if MODE == 'diff' else 'sec_killed'
alive = [key(r) for r in muts]
for k in range(1, KMAX + 1):
    tag = f'depth_{MODE}_k{k}'
    if MODE == 'diff' and k == 1:
        first = rows('kill'); run(tag, [i for i in alive if i not in first], 20, 240, 1)
        if not run(f'depth_diff_k1retry', [i for i in alive if first.get(i, {}).get('verdict') in ('timeout', 'error')], 40, 480, 1): pass
    elif not run(tag, alive, 20, 1800, k): break  # k>=2: ~100 s per mutant at k=3, so a larger per-family cap
    done = {}
    for t in ([ 'kill', tag, 'depth_diff_k1retry'] if (MODE == 'diff' and k == 1) else [tag]): done.update(rows(t))
    alive = [i for i in alive if done.get(i, {}).get('verdict') != KILL]
    print(k, 'remaining', len(alive), time.strftime('%H:%M'), flush=True)
