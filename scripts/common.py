"""Shared schema + helpers for data/ label builders."""
import csv, os, subprocess
FIELDS = ["id","source","chain","address","file_path","contract_name","label",
          "vuln_category","date","reference_url","license","source_commit"]
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
SRC = os.environ.get("SRC_DIR", "/tmp/ttvm-src")

def clone(url, name):
    d = os.path.join(SRC, name)
    if not os.path.isdir(d):
        os.makedirs(SRC, exist_ok=True)
        subprocess.run(["git","clone","-q","--depth","1",url,d], check=True)
    rev = subprocess.run(["git","-C",d,"rev-parse","HEAD"],capture_output=True,text=True).stdout.strip()
    return d, rev

def write(name, rows):
    p = os.path.join(DATA, name)
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in FIELDS})
    print(name, len(rows))
