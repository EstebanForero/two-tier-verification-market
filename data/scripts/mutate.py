"""Seeded, line-level Solidity mutation operators (Gambit/SuMo-style bug-pattern injection).
Each site = (line_no, operator, before, after). Mutants are single-site (order 1) plus seeded order-2 combos."""
import re, random
OPS = {}
def op(name, cls):
    def d(f): OPS[name] = (f, cls); return f
    return d
@op('DELREQ', 'access_control')          # delete a require/assert guard
def _delreq(l):
    m = re.search(r'\b(require|assert)\s*\(.*\)\s*;', l)
    if m and '.call' not in l and '.send(' not in l: return l[:m.start()] + '/*DELREQ*/' + l[m.end():]
@op('DELTHROW', 'access_control')        # delete "if (...) throw;" guard
def _delthrow(l):
    m = re.search(r'\bif\s*\(.*\)\s*\{?\s*throw\s*;\s*\}?', l)
    if m and '.call' not in l and '.send(' not in l: return l[:m.start()] + '/*DELTHROW*/' + l[m.end():]
@op('TXORIGIN', 'access_control')        # msg.sender auth -> tx.origin
def _txo(l):
    if re.search(r'msg\.sender\s*==|==\s*msg\.sender', l): return re.sub(r'msg\.sender(\s*==)|(==\s*)msg\.sender', lambda m: ('tx.origin'+m.group(1)) if m.group(1) else (m.group(2)+'tx.origin'), l, count=1)
@op('DELMOD', 'access_control')          # drop an access modifier from a function header
def _delmod(l):
    if re.search(r'\bfunction\b', l):
        m = re.search(r'\b(onlyOwner|onlyowner|ownerOnly|onlyAdmin)\b', l)
        if m: return l[:m.start()] + l[m.end():]
@op('UNCHK', 'unchecked_low_level_calls') # stop checking low-level call result
def _unchk(l):
    m = re.search(r'require\s*\(\s*([^;]*\.(call|send|delegatecall)\b[^;]*)\)\s*;', l)
    if m: return l[:m.start()] + m.group(1) + ';' + l[m.end():]
    m = re.search(r'if\s*\(\s*!\s*\(?\s*([^;]*\.(call|send)\b[^;]*?)\)?\s*\)\s*\{?\s*throw\s*;\s*\}?', l)
    if m: return l[:m.start()] + m.group(1) + ';' + l[m.end():]
    m = re.search(r'([\w\.\[\]]+)\.transfer\s*\(', l)
    if m and 'function' not in l: return l.replace('.transfer(', '.send(', 1)
@op('RELOP', 'arithmetic')               # off-by-one boundary
def _relop(l):
    if 'pragma' in l: return None
    for a, b in ((' >= ', ' > '), (' <= ', ' < '), (' > ', ' >= '), (' < ', ' <= ')):
        if a in l: return l.replace(a, b, 1)
@op('SAFEMATH', 'arithmetic')            # x.add(y) -> (x + y) etc. (drop overflow check)
def _sm(l):
    m = re.search(r'([\w\.\[\]]+)\.(add|sub|mul)\(([^()]*)\)', l)
    if m: return l[:m.start()] + f"({m.group(1)} {dict(add='+',sub='-',mul='*')[m.group(2)]} {m.group(3)})" + l[m.end():]
@op('REENT', 'reentrancy')               # move a state reset to after the external call (CEI violation)
def _reent(l): return None  # multi-line; handled in sites()

def sites(src):
    lines = src.split('\n'); out = []
    for i, l in enumerate(lines):
        if l.strip().startswith(('//', '*', '/*')): continue
        for name, (f, cls) in OPS.items():
            a = f(l)
            if a is not None and a != l: out.append((i, name, cls, l, a))
    for i, l in enumerate(lines):  # REENT: "x = 0;" / "-= amt;" line followed within 3 lines by .call.value/.send/.transfer
        if re.search(r'(=\s*0\s*;|-=)', l) and 'function' not in l:
            for j in range(i+1, min(i+4, len(lines))):
                if re.search(r'\.call\.value\(|\.send\(|\.transfer\(', lines[j]):
                    out.append((i, 'REENT', 'reentrancy', (i, j), None)); break
    return out

def apply(src, chosen):
    lines = src.split('\n')
    for (i, name, cls, before, after) in sorted(chosen, key=lambda s: -s[0]):
        if name == 'REENT':
            a, b = before; mv = lines.pop(a); lines.insert(b, mv)
        else: lines[i] = after
    return '\n'.join(lines)

def mutants(src, seed, n_order2=8):
    s = sites(src); rng = random.Random(seed); res = []
    for k, x in enumerate(s): res.append((f'm1_{k:03d}', [x]))
    pairs = [(a, b) for a in range(len(s)) for b in range(a+1, len(s)) if s[a][0] != s[b][0]]
    rng.shuffle(pairs)
    for a, b in pairs[:n_order2]: res.append((f'm2_{a:03d}_{b:03d}', [s[a], s[b]]))
    return res
