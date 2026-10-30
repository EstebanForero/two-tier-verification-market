"""Presumed-safe set (Ethereum mainnet). Candidates come ONLY from official deployment
sources fetched at build time (no hand-typed addresses):
  - Uniswap v2 / v3 deployment docs (docs.uniswap.org)
  - safe-global/safe-deployments v1.3.0 + v1.4.1 (MIT)
  - bgd-labs/aave-address-book AaveV3Ethereum.sol (MIT)
Objective filters (evidence written to data/presumed_safe_evidence.csv):
  C1 deployed >= 2 years before BUILD_DATE (creation tx timestamp, Blockscout API)
  C2 source verified on Blockscout
  C3 usage: >= 50 transactions to/from the address (one full page of Blockscout
     /addresses/<a>/transactions). The /counters endpoint was found to undercount
     badly (e.g. 3 for Uniswap SwapRouter), so it is recorded but not used.
  C4 address NOT a vulnerable contract in data/defihacklabs_exploits.csv
  C5 project has public audit reports (per-project, documented in README)
Label is 'presumed_safe' -- NOT verified safe."""
import re, json, csv, os, time, datetime as dt, urllib.request
from common import write, DATA
BUILD_DATE = dt.datetime(2026, 10, 30, tzinfo=dt.timezone.utc)
MIN_TX = 50  # one full Blockscout page
UA = {"User-Agent": "ttvm-labels/1.0"}
def get(u):
    for i in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode()
        except Exception as e: err = e; time.sleep(2 + 2*i)
    raise err
cands = []  # (name, address, project, reference_url, license)
def tables(u):
    for r in re.findall(r"<tr>(.*?)</tr>", get(u), re.S):
        yield [re.sub("<[^>]+>", "", x).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
U2 = "https://docs.uniswap.org/contracts/v2/reference/smart-contracts/v2-deployments"
for c in tables(U2):
    if len(c) == 3 and c[0] == "Mainnet":
        cands += [("UniswapV2Factory", c[1], "Uniswap v2", U2, "address from Uniswap docs"),
                  ("UniswapV2Router02", c[2], "Uniswap v2", U2, "address from Uniswap docs")]
U3 = "https://docs.uniswap.org/contracts/v3/reference/deployments/ethereum-deployments"
for c in tables(U3):
    if len(c) >= 2 and re.fullmatch(r"0x[0-9a-fA-F]{40}", c[1] or ""):
        cands.append((c[0], c[1], "Uniswap v3", U3, "address from Uniswap docs"))
    if len(c) == 4 and c[0] == "Ethereum" and c[2] == "WETH":
        cands.append(("WETH9", c[3], "WETH", U3, "address from Uniswap docs"))
SAFE = "https://raw.githubusercontent.com/safe-global/safe-deployments/main/src/assets/"
for v in ["v1.3.0", "v1.4.1"]:
    for f in json.loads(get(f"https://api.github.com/repos/safe-global/safe-deployments/contents/src/assets/{v}")):
        j = json.loads(get(SAFE + v + "/" + f["name"]))
        na = j.get("networkAddresses", {}).get("1")
        if na is None: continue
        types = na if isinstance(na, list) else [na]
        for t in types:
            a = j["deployments"][t]["address"] if "deployments" in j else (na if t.startswith("0x") else j.get("defaultAddress"))
            cands.append((f"{j['contractName']} {v} ({t})", a, "Safe", SAFE + v + "/" + f["name"], "MIT (safe-deployments)"))
AAVE = "https://raw.githubusercontent.com/bgd-labs/aave-address-book/main/src/AaveV3Ethereum.sol"
src = get(AAVE)
for name in ["POOL_ADDRESSES_PROVIDER","POOL","POOL_IMPL","POOL_CONFIGURATOR","ORACLE","ACL_MANAGER","COLLECTOR","WETH_GATEWAY"]:
    m = re.search(r"\b%s\s*=\s*(?:\w+\()?\s*(0x[0-9a-fA-F]{40})" % name, src)
    if m: cands.append((f"AaveV3Ethereum.{name}", m.group(1), "Aave v3", AAVE, "MIT (aave-address-book)"))
bad = {r["address"] for r in csv.DictReader(open(os.path.join(DATA, "defihacklabs_exploits.csv")))}
BS = "https://eth.blockscout.com/api/v2"
seen, out, ev = set(), [], []
for name, a, proj, ref, lic in cands:
    a = a.lower()
    if a in seen: continue
    seen.add(a)
    info = json.loads(get(f"{BS}/addresses/{a}"))
    cnt = json.loads(get(f"{BS}/addresses/{a}/counters"))
    txh = info.get("creation_transaction_hash") or info.get("creation_tx_hash")
    ts = json.loads(get(f"{BS}/transactions/{txh}"))["timestamp"] if txh else ""
    ntx = int(cnt.get("transactions_count") or 0)
    page = len(json.loads(get(f"{BS}/addresses/{a}/transactions")).get("items", []))
    age = (BUILD_DATE - dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))).days / 365.25 if ts else 0
    c = dict(C1_age_ge_2y=age >= 2, C2_verified=bool(info.get("is_verified")), C3_ge_50_txs=page >= MIN_TX, C4_not_in_dhl=a not in bad)
    ok = all(c.values())
    ev.append(dict(address=a, contract_name=name, project=proj, creation_tx=txh or "", deployed_at=ts,
                   age_years=round(age, 2), counter_tx_count=ntx, first_page_txs=page, **c, included=ok, reference_url=ref))
    if ok:
        out.append(dict(id=f"safe-{len(out)+1:03d}", source=f"presumed-safe/{proj}", chain="ethereum", address=a,
                        contract_name=name, label="presumed_safe", date=ts[:10], reference_url=ref, license=lic,
                        source_commit=f"blockscout creation tx {txh}"))
    time.sleep(0.3)
write("presumed_safe.csv", out)
with open(os.path.join(DATA, "presumed_safe_evidence.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, list(ev[0].keys())); w.writeheader(); w.writerows(ev)
print("candidates", len(ev), "included", len(out))
