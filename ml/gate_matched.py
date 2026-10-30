"""Length-matched gate: does the mutant-vs-X gate still separate once bytecode length is controlled?
For each X contract, pick up to R unused mutants with |log len diff| <= CAL (greedy nearest neighbour). On the matched set:
grouped 5-fold CV (groups = SmartBugs family / DApp / SolidiFI base contract), out-of-fold AUC for
 (a) length only, (b) opcode TF-IDF LR, (c) TF-IDF + log-length covariate; 95% CI = bootstrap over groups (1000x).
usage: python ml/gate_matched.py DS DAPPSCAN_DERIVED SOLIDIFI_DERIVED OUT_JSON"""
import sys, os, json, csv, re, numpy as np, scipy.sparse as sp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data', 'scripts')); import evmcfg
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
DS, DD, SD, OUT = sys.argv[1:5]; CAL, R, rng = 0.10, 2, np.random.default_rng(0)
def doc(h): return ' '.join(op for _, op, _ in evmcfg.disasm(h))
rows = list(csv.DictReader(open(f'{DS}/pairs.csv')))
for r in rows: r['hex'] = open(f"{DS}/bin/{r['family'].replace('/', '__')[:-4]}__{r['variant']}.bin").read(); r['g'] = 'sb:' + r['family']
mut = [r for r in rows if r['is_mutant'] == '1']; orig = [r for r in rows if r['is_mutant'] == '0']
real = json.load(open(f'{DD}/real_bugs.json'))
for r in real: r['hex'] = open(f"{DD}/bin/{r['runtime_sha256'][:16]}.bin").read(); r['g'] = 'dapp:' + r['dapp']
sfi = [r for r in json.load(open(f'{SD}/solidifi.json')) if r['ok'] and not r['dup']]
for r in sfi: r['hex'] = open(f"{SD}/bin/{r['sha'][:16]}.bin").read(); r['g'] = 'sfi:' + re.search(r'_(\d+)\.sol$', r['file']).group(1)
ll = lambda r: np.log(len(r['hex']) / 2)
def match(others, pool, same_family=False):
    used, P, N = set(), [], []
    for o in sorted(others, key=ll):
        c = [m for m in pool if id(m) not in used and abs(ll(m) - ll(o)) <= CAL and (not same_family or m['g'] == o['g'])]
        c = sorted(c, key=lambda m: abs(ll(m) - ll(o)))[:R]
        if c: N.append(o); P += c; used |= {id(m) for m in c}
    return P, N
def auc_ci(y, p, g):
    a = roc_auc_score(y, p); G = np.unique(g); idx = {k: np.where(g == k)[0] for k in G}; bs = []
    for _ in range(1000):
        s = np.concatenate([idx[k] for k in rng.choice(G, len(G))])
        if 0 < y[s].sum() < len(s): bs.append(roc_auc_score(y[s], p[s]))
    return dict(auc=round(float(a), 3), ci95=[round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)])
def evalset(P, N, name):
    S = P + N; y = np.array([1] * len(P) + [0] * len(N)); g = np.array([r['g'] for r in S]); L = np.array([[ll(r)] for r in S])
    docs = [doc(r['hex']) for r in S]; o = {k: np.zeros(len(S)) for k in ('length', 'opcode', 'opcode+length')}
    for tr, te in GroupKFold(5).split(S, y, g):
        o['length'][te] = LogisticRegression(class_weight='balanced').fit(L[tr], y[tr]).predict_proba(L[te])[:, 1]
        v = TfidfVectorizer(ngram_range=(1, 3), min_df=2, max_features=50000, sublinear_tf=True, token_pattern=r'\S+')
        Xtr = v.fit_transform([docs[i] for i in tr]); Xte = v.transform([docs[i] for i in te])
        o['opcode'][te] = LogisticRegression(max_iter=2000, class_weight='balanced').fit(Xtr, y[tr]).predict_proba(Xte)[:, 1]
        mu, sd = L[tr].mean(), L[tr].std() + 1e-9
        Xtr2 = sp.hstack([Xtr, (L[tr] - mu) / sd]).tocsr(); Xte2 = sp.hstack([Xte, (L[te] - mu) / sd]).tocsr()
        o['opcode+length'][te] = LogisticRegression(max_iter=2000, class_weight='balanced').fit(Xtr2, y[tr]).predict_proba(Xte2)[:, 1]
    return {name: dict(n_mutant=len(P), n_other=len(N), groups_mutant=len(set(g[y == 1])), groups_other=len(set(g[y == 0])),
                       mean_abs_loglen_diff=round(float(abs(np.mean(L[y == 1]) - np.mean(L[y == 0]))), 4),
                       **{k: auc_ci(y, v, g) for k, v in o.items()})}
res = dict(method=dict(caliper_loglen=CAL, mutants_per_other=R, cv='GroupKFold(5)', ci='group bootstrap 1000'))
old = [r for r in real if r['solc'] < '0.6']
res.update(evalset(*match(old, mut), 'mutant_vs_dappscan_solc_lt0.6'))
res.update(evalset(*match(real, mut), 'mutant_vs_dappscan_all'))
res.update(evalset(*match(sfi, mut), 'mutant_vs_solidifi'))
res.update(evalset(*match(orig, mut, same_family=True), 'mutant_vs_own_original'))
res['unmatched_counts'] = dict(dappscan_lt06=len(old), dappscan_all=len(real), solidifi=len(sfi), originals=len(orig), mutants=len(mut))
json.dump(res, open(OUT, 'w'), indent=1); print(json.dumps(res, indent=1))
