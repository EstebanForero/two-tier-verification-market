"""Opcode n-gram TF-IDF + logistic regression screener and mutant-vs-real gate. Frozen family / DApp splits.
usage: python ml/baseline.py DS_DIR DAPPSCAN_DERIVED OUT_JSON"""
import sys, os, json, csv, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data', 'scripts')); import evmcfg
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss, roc_curve
DS, DD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CLASSES = ['access_control', 'arithmetic', 'reentrancy', 'unchecked_low_level_calls']
SWC2C = {'SWC-101': 'arithmetic', 'SWC-104': 'unchecked_low_level_calls', 'SWC-107': 'reentrancy', 'SWC-105': 'access_control',
         'SWC-112': 'access_control', 'SWC-115': 'access_control'}  # 113/114/128 (DoS, front-running) -> no screener class
def doc(hexcode): return ' '.join(op for _, op, _ in evmcfg.disasm(hexcode))  # PUSH args dropped
def ece(y, p, b=10):
    e = 0; idx = np.minimum((p * b).astype(int), b - 1)
    for i in range(b):
        m = idx == i
        if m.any(): e += m.mean() * abs(y[m].mean() - p[m].mean())
    return float(e)
def fnr_at_fpr(y, p, f):
    if y.min() == y.max(): return None
    fpr, tpr, _ = roc_curve(y, p); ok = fpr <= f
    return float(1 - tpr[ok].max()) if ok.any() else 1.0
def metrics(y, p):
    y = np.asarray(y); p = np.clip(np.asarray(p), 1e-6, 1 - 1e-6)
    return dict(n=int(len(y)), pos=int(y.sum()), auc=float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else None,
                brier=float(brier_score_loss(y, p)), logloss=float(log_loss(y, p, labels=[0, 1])), ece=ece(y, p),
                fnr_at_fpr5=fnr_at_fpr(y, p, .05), fnr_at_fpr0_5=fnr_at_fpr(y, p, .005))
# --- SmartBugs originals + mutants
rows = list(csv.DictReader(open(f'{DS}/pairs.csv')))
for r in rows:
    stem = r['family'].replace('/', '__')[:-4]; r['hex'] = open(f"{DS}/bin/{stem}__{r['variant']}.bin").read()
    labs = set(filter(None, r['sb_labels'].split('|'))) | set(filter(None, r['injected_class'].split('|'))); r['labs'] = labs
# --- DAppSCAN real positives (positive-only labels; negatives for class c = contracts labelled only with other classes)
real = json.load(open(f'{DD}/real_bugs.json'))
for r in real:
    r['hex'] = open(f"{DD}/bin/{r['runtime_sha256'][:16]}.bin").read(); r['labs'] = {SWC2C[s] for s in r['swcs'].split('|') if s in SWC2C}
vec = TfidfVectorizer(ngram_range=(1, 3), min_df=2, max_features=50000, sublinear_tf=True, token_pattern=r'\S+')
Xs = vec.fit_transform([doc(r['hex']) for r in rows if r['split'] == 'train'])
X = lambda rs: vec.transform([doc(r['hex']) for r in rs])
sp = {s: [r for r in rows if r['split'] == s] for s in ('train', 'val', 'test')}
res = {'n': {s: len(v) for s, v in sp.items()}, 'screener': {}, 'gate': {}}
Xtr, Xva, Xte = Xs, X(sp['val']), X(sp['test']); Xre = X(real)
for c in CLASSES:
    y = lambda rs: np.array([c in r['labs'] for r in rs], int)
    clf = LogisticRegression(C=1.0, max_iter=2000, class_weight='balanced').fit(Xtr, y(sp['train']))
    iso = IsotonicRegression(out_of_bounds='clip', y_min=0, y_max=1).fit(clf.predict_proba(Xva)[:, 1], y(sp['val']))
    pt = iso.predict(clf.predict_proba(Xte)[:, 1]); yt = y(sp['test'])
    mut = np.array([r['is_mutant'] == '1' for r in sp['test']])
    pr = iso.predict(clf.predict_proba(Xre)[:, 1]); yr = y(real)
    res['screener'][c] = dict(test_all=metrics(yt, pt), test_mutant_only=metrics(yt[mut], pt[mut]), test_orig_only=metrics(yt[~mut], pt[~mut]),
                              real_dappscan_all=metrics(yr, pr), real_dappscan_test_split=metrics(yr[[r['split'] == 'test' for r in real]], pr[[r['split'] == 'test' for r in real]]))
# --- Gate A: SmartBugs original vs its own mutants (same family, same solc) -> AUC on family-split test
yA = lambda rs: np.array([r['is_mutant'] == '1' for r in rs], int)
gA = LogisticRegression(C=1.0, max_iter=2000, class_weight='balanced').fit(Xtr, yA(sp['train']))
res['gate']['A_smartbugs_orig_vs_mutant'] = metrics(yA(sp['test']), gA.predict_proba(Xte)[:, 1])
# --- Gate B: SmartBugs mutants vs DAppSCAN real-bug contracts, solc matched (<0.6 only), split by family / DApp
def B(rs_m, rs_r): return rs_m + rs_r, np.array([1] * len(rs_m) + [0] * len(rs_r))
old = [r for r in real if r['solc'] < '0.6']
mt = {s: [r for r in sp[s] if r['is_mutant'] == '1'] for s in sp}; rl = {s: [r for r in old if r['split'] == s] for s in ('train', 'val', 'test')}
vb = TfidfVectorizer(ngram_range=(1, 3), min_df=2, max_features=50000, sublinear_tf=True, token_pattern=r'\S+')
trs, ytr = B(mt['train'], rl['train']); Xb = vb.fit_transform([doc(r['hex']) for r in trs])
gB = LogisticRegression(C=1.0, max_iter=2000, class_weight='balanced').fit(Xb, ytr)
tes, yte = B(mt['test'], rl['test'] + rl['val'])
res['gate']['B_mutant_vs_dappscan_solc_lt_0_6'] = dict(metrics(yte, gB.predict_proba(vb.transform([doc(r['hex']) for r in tes]))[:, 1]),
    n_real_train=len(rl['train']), n_real_eval=len(rl['test']) + len(rl['val']), note='real eval = DAppSCAN val+test DApps (test alone too small)')
res['gate']['B_solc_versions'] = dict(mutants=sorted({r['solc'] for r in mt['train']}), real=sorted({r['solc'] for r in old}))
json.dump(res, open(OUT, 'w'), indent=1); print(json.dumps(res, indent=1))
