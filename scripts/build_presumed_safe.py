"""Presumed-safe set: a small, hand-chosen list of long-lived, widely used, audited
Ethereum mainnet contracts. Addresses are fetched at build time from the projects'
own deployment sources (not typed in) and any address that also appears as a
DeFiHackLabs vulnerable contract is dropped. Label is 'presumed_safe' -- NOT verified safe."""
import re, json, csv, os, urllib.request
from common import write, DATA
UNI = "https://docs.uniswap.org/contracts/v3/reference/deployments/ethereum-deployments"
SAFE = "https://raw.githubusercontent.com/safe-global/safe-deployments/main/src/assets/v1.3.0/{}.json"
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"curl/8"})).read().decode()
WANT_UNI = {"UniswapV3Factory":"2021-05","NonfungiblePositionManager":"2021-05","SwapRouter":"2021-05","Permit2":"2022-11"}
rows = []
t = get(UNI)
for r in re.findall(r"<tr>(.*?)</tr>", t, re.S):
    c = [re.sub("<[^>]+>","",x).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
    if len(c) >= 2 and c[0] in WANT_UNI:
        rows.append(dict(contract_name=c[0], address=c[1], date=WANT_UNI.pop(c[0]), reference_url=UNI,
                         license="address facts from Uniswap docs (GPL-2.0/BUSL code not copied)"))
    if len(c) == 4 and c[0] == "Ethereum" and c[2] == "WETH":
        rows.append(dict(contract_name="WETH9", address=c[3], date="2017-12", reference_url=UNI,
                         license="address facts from Uniswap docs"))
for n, nm in [("gnosis_safe","GnosisSafe 1.3.0 singleton"),("proxy_factory","GnosisSafeProxyFactory 1.3.0")]:
    u = SAFE.format(n); j = json.loads(get(u))
    a = j["deployments"]["canonical"]["address"] if "deployments" in j else j["defaultAddress"]
    rows.append(dict(contract_name=nm, address=a, date="2021-05", reference_url=u, license="MIT (safe-deployments)"))
bad = {r["address"] for r in csv.DictReader(open(os.path.join(DATA,"defihacklabs_exploits.csv")))}
out = []
for r in rows:
    r["address"] = r["address"].lower()
    if r["address"] in bad: print("dropped (in DeFiHackLabs):", r); continue
    out.append(dict(r, id=f"safe-{len(out)+1:03d}", source="presumed-safe", chain="ethereum",
                    label="presumed_safe", vuln_category=""))
write("presumed_safe.csv", out)
