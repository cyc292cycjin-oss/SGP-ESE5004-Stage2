"""X20 ②2 数据：OSM 预建库（osm-plus-prebuilt 0.1.1）国内交流重复组 + OSM 官方 API way 标签（允许的下载 (a)，合计 <= 50 MB）。
重复键同 X10 04b_x10_ac_reconstruct.py:43-46：(way, min(bus0,bus1), max(bus0,bus1), voltage, round(length))。只取 AC（dc == False）、两端同国的组。
输出：cache/osm/DUP_GROUPS_V5.csv、downloads/osm/ways_<n>.json、downloads/osm/OSM_API_LOG.tsv、cache/osm/WAY_TAGS_V5.csv。"""
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

CODE = Path(r"D:\ResearchWorkspaces\ASEAN\work\p1_v5_x03_renew_20261111\cache\code")
D = Path(r"D:\ResearchWorkspaces\ASEAN\work\p1_v5_x20_20261111")
PRE = CODE / "data/osm-plus-prebuilt/0.1.1"
OUT_C = D / "cache/osm"; OUT_D = D / "downloads/osm"
OUT_C.mkdir(parents=True, exist_ok=True); OUT_D.mkdir(parents=True, exist_ok=True)
UA = "research-network-data-check/1.0 (python-urllib)"
MAX_BYTES = 50 * 1024 * 1024

lines = pd.read_csv(PRE / "all_lines_build_network.csv", dtype={"line_id": str, "bus0": str, "bus1": str})
buses = pd.read_csv(PRE / "all_buses_build_network.csv", dtype={"bus_id": str})
cty = buses.set_index("bus_id")["country"].to_dict()
ac = lines[~lines["dc"].astype(str).str.lower().isin(["true", "1"])].copy()
ac["way"] = ac["line_id"].str.split("-").str[0]
ac["b0"] = ac[["bus0", "bus1"]].min(axis=1); ac["b1"] = ac[["bus0", "bus1"]].max(axis=1)
ac["c0"] = ac["bus0"].map(cty); ac["c1"] = ac["bus1"].map(cty)
ac["len_r"] = ac["length"].round(0)
key = ["way", "b0", "b1", "voltage", "len_r"]
g = ac.groupby(key)
dup = ac[g["line_id"].transform("size") > 1].copy()
dup = dup[dup.c0 == dup.c1]
summ = dup.groupby(key).agg(country=("c0", "first"), rows=("line_id", "size"), circuits_each=("circuits", "first"),
                            circuits_all_equal=("circuits", lambda s: s.nunique() == 1), ids=("line_id", lambda s: ";".join(sorted(s)))).reset_index()
summ.to_csv(OUT_C / "DUP_GROUPS_V5.csv", index=False)
print("dup groups", len(summ), "rows", int(summ.rows.sum()))
print(summ.groupby("country").agg(groups=("rows", "size"), rows=("rows", "sum")).to_string())
ways = sorted({w for w in summ.way if w.isdigit() and not w.startswith("1000000")})
print("ways to fetch", len(ways), "(osm-plus manual ids 1000000xx skipped:", sum(1 for w in summ.way if w.startswith("1000000")), ")")

log = []; total = 0; recs = []
for i in range(0, len(ways), 100):
    batch = ways[i:i + 100]
    url = "https://api.openstreetmap.org/api/0.6/ways.json?ways=" + ",".join(batch)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read(); status = r.status
    except urllib.error.HTTPError as e:   # 404 / 410 when a way was deleted: fetch one by one
        body = b""; status = e.code
    if status != 200:
        for w in batch:
            u1 = f"https://api.openstreetmap.org/api/0.6/way/{w}.json"
            try:
                with urllib.request.urlopen(urllib.request.Request(u1, headers={"User-Agent": UA}), timeout=60) as r1:
                    b1 = r1.read(); s1 = r1.status
            except urllib.error.HTTPError as e1:
                b1 = b""; s1 = e1.code
            total += len(b1)
            f1 = OUT_D / f"way_{w}.json"; f1.write_bytes(b1)
            log.append(dict(utc=t0, url=u1, status=s1, bytes=len(b1), sha256=hashlib.sha256(b1).hexdigest(), file=f1.name))
            if s1 == 200:
                recs += json.loads(b1)["elements"]
            time.sleep(1.0)
    else:
        total += len(body)
        f = OUT_D / f"ways_{i // 100:03d}.json"; f.write_bytes(body)
        log.append(dict(utc=t0, url=url, status=status, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), file=f.name))
        recs += json.loads(body)["elements"]
    if total > MAX_BYTES:
        raise SystemExit(f"download cap exceeded: {total} B")
    time.sleep(1.0)
pd.DataFrame(log).to_csv(OUT_D / "OSM_API_LOG.tsv", sep="\t", index=False)
rows = []
for e in recs:
    t = e.get("tags", {})
    rows.append(dict(way=str(e["id"]), version=e.get("version"), timestamp=e.get("timestamp"), power=t.get("power"), voltage=t.get("voltage"),
                     cables=t.get("cables"), circuits=t.get("circuits"), name=t.get("name"), operator=t.get("operator")))
tags = pd.DataFrame(rows)
tags.to_csv(OUT_C / "WAY_TAGS_V5.csv", index=False)
missing = sorted(set(ways) - set(tags.way))
print("fetched", len(tags), "missing", len(missing), "bytes", total, "requests", len(log))
print("cables present", int(tags.cables.notna().sum()), "circuits present", int(tags.circuits.notna().sum()))
