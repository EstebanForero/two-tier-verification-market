"""Proof-check cost of Halmos SMT queries: for each dumped .smt2, (1) cvc5 solve, (2) cvc5 Alethe proof -> Carcara check,
(3) cvc5 CPC proof -> Ethos check (CPC signature from cvc5 source at the same tag). Records times, proof sizes, outcomes, and
which theories each query uses (arrays, UF, BV). usage: python proofcost.py DUMP_DIR OUT_CSV [timeout_s]
Tools via env: CVC5, CARCARA, ETHOS, CPC_EO (path to proofs/eo/cpc/Cpc.eo)."""
import csv, os, re, subprocess, sys, time, pathlib, tempfile
D, OUT = pathlib.Path(sys.argv[1]), sys.argv[2]; TO = int(sys.argv[3]) if len(sys.argv) > 3 else 120
CVC5, CAR, ETH, CPC = (os.environ[k] for k in ('CVC5', 'CARCARA', 'ETHOS', 'CPC_EO'))
def run(cmd, to=TO):
    t = time.time()
    try: p = subprocess.run(cmd, capture_output=True, text=True, timeout=to); return p.stdout, p.stderr, round(time.time() - t, 3), p.returncode
    except subprocess.TimeoutExpired: return '', 'TIMEOUT', round(time.time() - t, 3), -9
def body(f):  # drop get-model so proof mode works
    return re.sub(r'\(get-model\)', '', f.read_text())
rows = []
import random
QS = sorted(D.rglob('*.smt2')); random.Random(0).shuffle(QS)  # deterministic interleave across sources; partial runs are an unbiased sample
KEYS = None
def flush():
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(OUT, 'w', newline='') as fh: w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
for f in QS:
    src = body(f); tmp = pathlib.Path(tempfile.mkdtemp()) / 'q.smt2'; tmp.write_text(src)
    r = dict(query=str(f.relative_to(D)), bytes=len(src), arrays=int('Array' in src), uf=int(bool(re.search(r'\(declare-fun \S+ \(\(?_ BitVec', src))),
             bvmul_div=int(bool(re.search(r'bv(mul|udiv|urem|sdiv|srem)', src))))
    o, e, t, _ = run([CVC5, '--lang=smt2', str(tmp)]); r.update(result=(o.strip().splitlines() or ['timeout' if e == 'TIMEOUT' else 'err'])[0], solve_s=t)
    if r['result'] != 'unsat': rows.append(r); print(r, flush=True); flush(); continue
    for fmt, chk in (('alethe', 'carcara'), ('cpc', 'ethos')):
        pf = tmp.with_suffix(f'.{fmt}')
        extra = ['--proof-alethe-res-pivots'] if fmt == 'alethe' else []
        o, e, t, rc = run([CVC5, '--lang=smt2', '--dump-proofs', f'--proof-format-mode={fmt}', *extra, str(tmp)])
        lines = o.splitlines(); proof = '\n'.join(lines[1:]).strip() if lines and lines[0] == 'unsat' else ''
        if proof.startswith('(') and proof.endswith(')'): proof = proof[1:-1]  # cvc5 wraps the proof in one outer list
        pf.write_text(proof); r[f'{fmt}_gen_s'] = t; r[f'{fmt}_bytes'] = len(proof); r[f'{fmt}_steps'] = proof.count('(step') if fmt == 'alethe' else proof.count('(step')
        r[f'{fmt}_gen_note'] = '' if proof else (e.strip().splitlines() or ['no proof'])[-1][:160]
        if not proof: r[f'{fmt}_check'] = 'no_proof'; continue
        if fmt == 'alethe': cmd = [CAR, 'check', '--expand-let-bindings', str(pf), str(tmp)]
        else:
            ef = tmp.with_suffix('.eo'); ef.write_text(f'(include "{CPC}")\n' + proof); cmd = [ETH, str(ef)]
        o, e, t, rc = run(cmd); out = (o + e).strip()
        r[f'{fmt}_check_s'] = t; r[f'{fmt}_check'] = 'TIMEOUT' if e == 'TIMEOUT' else (' | '.join(out.splitlines()[-2:])[:200] if out else f'rc={rc}')
    rows.append(r); print(r, flush=True); flush()
keys = sorted({k for r in rows for k in r}, key=lambda k: list(rows[0]).index(k) if k in rows[0] else 99)
with open(OUT, 'w', newline='') as fh: w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
