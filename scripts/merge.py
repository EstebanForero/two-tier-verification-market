import csv, os
from common import DATA, FIELDS
out = os.path.join(DATA, "labels.csv")
n = 0
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, FIELDS); w.writeheader()
    for p in ["defihacklabs_exploits.csv","solidifi_injected.csv","presumed_safe.csv","solodit_audit_findings.csv"]:
        if not os.path.exists(os.path.join(DATA,p)): continue
        for r in csv.DictReader(open(os.path.join(DATA,p))): w.writerow(r); n += 1
print("labels.csv", n)
