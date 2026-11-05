"""V4 W07 G1 (MY): fetch the UNSD public SDMX energy data for Malaysia (A5 exception: same interface as the repository
research_inputs/assembly_v1/sources/unsd_targeted/, no login). Raw responses are stored unchanged with a receipt (URL, UTC time, HTTP status,
headers, bytes, SHA256). Two requests: (1) every commodity and transaction for 2019 (CONVERSION_FACTOR per observation);
(2) coal and solid-biomass commodities 2010-2022 (series and conversion factors over time).

    python scripts/v4g1_sdmx_fetch.py          (WSL python; writes G1/sdmx/)
"""
import datetime as dt
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "sdmx"
BASE = "https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY,/"
REQ = {
    "MY_2019_all.xml": BASE + "A.458../?startPeriod=2019&endPeriod=2019",
    "MY_2010_2022_coal_biomass.xml": BASE + "A.458.0100+0110+0121+0129+0200+0210+0220+0311+0350+5110+5120+5140+5150+5160./?startPeriod=2010&endPeriod=2022",
}


def fetch(name, url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-data-client/1.0", "Accept": "application/vnd.sdmx.genericdata+xml;version=2.1"})
    t0 = dt.datetime.now(dt.timezone.utc).isoformat()
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read(); status = r.status; headers = dict(r.headers); final = r.geturl()
    p = OUT / name
    p.write_bytes(body)
    rec = dict(file=name, url=url, utc=t0, http_status=status, headers=headers, final_url=final, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), status="RETRIEVED")
    (OUT / (name + ".receipt.json")).write_text(json.dumps(rec, indent=1) + "\n")
    print(name, status, len(body), rec["sha256"])


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for k, u in REQ.items():
        if (OUT / k).exists() and "--force" not in sys.argv:
            print("exists, skipped:", k); continue
        fetch(k, u)
