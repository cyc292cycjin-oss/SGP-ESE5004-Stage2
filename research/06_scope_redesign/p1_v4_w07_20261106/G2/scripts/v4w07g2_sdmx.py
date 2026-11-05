"""G2: query the public UNSD SDMX interface (A5 exception; same endpoint as research_inputs/assembly_v1/sources/unsd_targeted/) for Viet Nam.

    python scripts/v4w07g2_sdmx.py

One request per commodity group, all transactions (wildcard), 2005-2022. The raw response is saved byte for byte under sdmx/ with a receipt
(url, final url, UTC time, HTTP status, headers, bytes, SHA256), as in unsd_targeted/*.receipt.json. No login, no key.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "sdmx"
BASE = "https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY,/A.704.{c}./?startPeriod=2005&endPeriod=2022"
GROUPS = {
    "VN_coal": "0100+0110+0121+0129+0311+0350+0371",
    "VN_biomass": "5110+5120+5130+5140+5150+5160+5300+6100+6200",
    "VN_gas_elec": "3000+7000+7000T+EC",
    "VN_oil_ind": "4630+4670+4680+4694",
}


def fetch(name: str, codes: str):
    url = BASE.format(c=codes)
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.sdmx.genericdata+xml;version=2.1", "User-Agent": "research-client"})
    t = dt.datetime.now(dt.timezone.utc).isoformat()
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read(); status = r.status; final = r.geturl(); headers = dict(r.headers.items())
    p = OUT / f"{name}.xml"
    p.write_bytes(body)
    rec = dict(file=p.name, url=url, utc=t, http_status=status, final_url=final, headers=headers, bytes=len(body),
               sha256=hashlib.sha256(body).hexdigest(), status="RETRIEVED")
    (OUT / f"{name}.xml.receipt.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(name, status, len(body), rec["sha256"][:16])


def main():
    OUT.mkdir(exist_ok=True)
    for name, codes in GROUPS.items():
        if (OUT / f"{name}.xml").exists() and "--force" not in sys.argv:
            print(name, "exists, skipped"); continue
        fetch(name, codes); time.sleep(2)


if __name__ == "__main__":
    main()
