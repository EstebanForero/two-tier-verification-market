"""Real exploit labels from DeFiHackLabs (Apache-2.0). Metadata only; no PoC code copied.
One row per PoC file src/test/YYYY-MM/<Name>_exp.sol. Vulnerable address parsed from the
PoC's @KeyInfo header ("Vuln Contract"/"Vulnerable Contract") when present; category taken
from the README heading text after ' - ' (free text, truncated) when the PoC is listed there."""
import os, re, glob
from common import clone, write
REPO = "https://github.com/SunWeb3Sec/DeFiHackLabs"
d, rev = clone(REPO + ".git", "DeFiHackLabs")
EXPL = {"etherscan.io":"ethereum","bscscan.com":"bsc","polygonscan.com":"polygon","arbiscan.io":"arbitrum",
 "optimistic.etherscan.io":"optimism","basescan.org":"base","snowtrace.io":"avalanche","ftmscan.com":"fantom",
 "blastscan.io":"blast","lineascan.build":"linea","scrollscan.com":"scroll","gnosisscan.io":"gnosis",
 "era.zksync.network":"zksync","snowscan.xyz":"avalanche","sonicscan.org":"sonic","explorer.mantle.xyz":"mantle","mantlescan.xyz":"mantle"}
# README headings: ### YYYYMMDD Name - description ... then a link to src/test/...file
heads = {}
for rd in [os.path.join(d,"README.md")] + glob.glob(os.path.join(d,"past","*","README.md")):
    cur = None
    for line in open(rd, encoding="utf-8", errors="replace"):
        m = re.match(r"^### (\d{8}) (.+)$", line.strip())
        if m: cur = m.groups(); continue
        m = re.search(r"\((src/test/[^)]+\.sol)\)", line)
        if m and cur and m.group(1) not in heads: heads[m.group(1)] = cur
rows = []
vuln_re = re.compile(r"Vuln(?:erable)?\s*Contract[s]?\s*[:\-]?\s*(https?://[^\s)\]]+)", re.I)
for f in sorted(glob.glob(os.path.join(d,"src","test","*","*.sol"))):
    rel = os.path.relpath(f, d)
    ym = os.path.basename(os.path.dirname(f))
    if not re.match(r"\d{4}-\d{2}$", ym): continue
    txt = open(f, encoding="utf-8", errors="replace").read(6000)
    url = (vuln_re.search(txt) or [None, ""])[1]
    chain, addr = "", ""
    m = re.match(r"https?://(?:www\.)?([^/]+)/(?:address|token)/(0x[0-9a-fA-F]{40})", url)
    if m: chain = EXPL.get(m.group(1), m.group(1)); addr = m.group(2).lower()
    h = heads.get(rel)
    date = f"{h[0][:4]}-{h[0][4:6]}-{h[0][6:]}" if h else ym
    name, cat = (h[1].split(" - ",1)+[""])[:2] if h else (os.path.basename(f).replace("_exp.sol",""), "")
    rows.append(dict(id=f"dhl-{len(rows)+1:05d}", source="DeFiHackLabs", chain=chain, address=addr,
        file_path=rel, contract_name=name.strip(), label="exploited", vuln_category=cat.strip()[:200],
        date=date, reference_url=f"{REPO}/blob/{rev}/{rel}", license="Apache-2.0", source_commit=rev))
write("defihacklabs_exploits.csv", rows)
