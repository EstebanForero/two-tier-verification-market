"""Mutant-vs-other gate classifiers with confound controls. Same features/model as baseline.py (opcode 1-3gram TF-IDF + LR).
usage: python ml/gate.py DS_DIR DAPPSCAN_DERIVED SOLIDIFI_DERIVED OUT_JSON   (external data stays outside the repo)
For each gate we also report a 1-feature baseline (log bytecode length) to show how much is just corpus/size."""
import sys, os, json, csv, hashlib, re, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data', 'scripts')); import evmcfg
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
DS, DD, SD, OUT = sys.argv[1:5]
def doc(h): return ' '.join(op for _, op, _ in evmcfg.disasm(h))
def split(key): v = int(hashlib.sha256(key.encode()).hexdigest(), 16) % 100; return 'train' if v < 70 else ('val' if v < 85 else 'test')
rows = list(csv.DictReader(open(f'{DS}/pairs.csv')))
for r in rows: r['hex'] = open(f"{DS}/bin/{r['family'].replace('/', '__')[:-4]}__{r['variant']}.bin").read()
mut = [r for r in rows if r['is_mutant'] == '1']; orig = [r for r in rows if r['is_mutant'] == '0']
real = json.load(open(f'{DD}/real_bugs.json'))
for r in real: r['hex'] = open(f"{DD}/bin/{r['runtime_sha256'][:16]}.bin").read()
sfi = [r for r in json.load(open(f'{SD}/solidifi.json')) if r['ok'] and not r['dup']]
for r in sfi:
    r['hex'] = open(f"{SD}/bin/{r['sha'][:16]}.bin").read()
    r['split'] = split('solidifi/' + re.search(r'_(\d+)\.sol$', r['file']).group(1))  # same base contract -> same split
def gate(pos, neg, name, note=''):
    tr = [r for r in pos + neg if r['split'] == 'train']; te = [r for r in pos + neg if r['split'] in ('val', 'test')]
    ytr = np.array([1 if r in pos else 0 for r in tr]); yte = np.array([1 if r in pos else 0 for r in te])
    if len(set(ytr)) < 2 or len(set(yte)) < 2: return {name: dict(skipped='one class missing', n_pos=len(pos), n_neg=len(neg))}
    v = TfidfVectorizer(ngram_range=(1, 3), min_df=2, max_features=50000, sublinear_tf=True, token_pattern=r'\S+')
    m = LogisticRegression(C=1.0, max_iter=2000, class_weight='balanced').fit(v.fit_transform([doc(r['hex']) for r in tr]), ytr)
    p = m.predict_proba(v.transform([doc(r['hex']) for r in te]))[:, 1]
    L = lambda rs: np.log([[len(r['hex'])] for r in rs])
    pl = LogisticRegression(class_weight='balanced').fit(L(tr), ytr).predict_proba(L(te))[:, 1]
    return {name: dict(auc=float(roc_auc_score(yte, p)), auc_length_only=float(roc_auc_score(yte, pl)),
                       n_train=len(tr), n_eval=len(te), eval_pos_mutant=int(yte.sum()), eval_neg=int(len(yte) - yte.sum()), note=note)}
res = {}
inter = lambda a, b: sorted({r['solc'] for r in a} & {r['solc'] for r in b})
res.update(gate(mut, orig, 'A_mutant_vs_own_smartbugs_original', 'eval = val+test families'))
old = [r for r in real if r['solc'] < '0.6']; vs = inter(mut, old)
res.update(gate(mut, old, 'B_mutant_vs_dappscan_lt0.6'))
res.update(gate([r for r in mut if r['solc'] in vs], [r for r in old if r['solc'] in vs], 'B2_mutant_vs_dappscan_exact_solc', f'solc in {vs}'))
res.update(gate(mut, sfi, 'C_mutant_vs_solidifi', 'SolidiFI = bugs injected into real Etherscan code (also synthetic)'))
vc = inter(mut, sfi)
res.update(gate([r for r in mut if r['solc'] in vc], [r for r in sfi if r['solc'] in vc], 'C2_mutant_vs_solidifi_exact_solc', f'solc in {vc}'))
res['counts'] = dict(mutants=len(mut), originals=len(orig), dappscan_lt06=len(old), solidifi=len(sfi), defihacklabs='not fetched')
json.dump(res, open(OUT, 'w'), indent=1); print(json.dumps(res, indent=1))
