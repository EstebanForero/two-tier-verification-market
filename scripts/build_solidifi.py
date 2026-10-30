"""Injected-bug labels from SolidiFI-benchmark (MIT for the tool/benchmark; original
contracts came from Etherscan and retain their original licenses -> we store only
paths + bug locations, not contract source). One row per injected bug (BugLog line)."""
import os, csv, glob
from common import clone, write
REPO = "https://github.com/smartbugs/SolidiFI-benchmark"
d, rev = clone(REPO + ".git", "SolidiFI-benchmark")
rows = []
for cat in sorted(os.listdir(os.path.join(d,"buggy_contracts"))):
    cd = os.path.join(d,"buggy_contracts",cat)
    for log in sorted(glob.glob(os.path.join(cd,"BugLog_*.csv")), key=lambda p:int(p.split("_")[-1][:-4])):
        n = log.split("_")[-1][:-4]
        sol = f"buggy_contracts/{cat}/buggy_{n}.sol"
        if not os.path.exists(os.path.join(d,sol)): continue
        for r in csv.DictReader(open(log, encoding="utf-8", errors="replace")):
            rows.append(dict(id=f"solidifi-{len(rows)+1:05d}", source="SolidiFI-benchmark", chain="",
                file_path=f"{sol}#L{r.get('loc','')}+{r.get('length','')}", contract_name=f"buggy_{n}",
                label="injected_bug", vuln_category=cat, date="",
                reference_url=f"{REPO}/blob/{rev}/{sol}", license="MIT (benchmark); original contracts retain Etherscan licenses",
                source_commit=rev))
write("solidifi_injected.csv", rows)
