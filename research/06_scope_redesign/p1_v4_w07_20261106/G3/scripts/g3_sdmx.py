"""G3 (v4 W07, B-G3): UNSD SDMX query for TH, PH, SG - the only download the instruction allows (A5).

    python scripts/g3_sdmx.py            (WSL pypsa-earth python; network access to data.un.org)

Same public interface as research_inputs/assembly_v1/sources/unsd_targeted/ (no login): dataflow UNSD,DF_UNDATA_ENERGY, key
A.<area>.<commodities>.<all transactions>, 2015-2022. Commodities: the coal family (0100 hard coal, 0110 anthracite, 0121 coking coal,
0129 other bituminous, 0200 brown coal, 0210 sub-bituminous, 0220 lignite, 0311 coke-oven coke, 4694 petroleum coke) and solid biofuels
(5110 fuelwood, 5120 bagasse, 5140 black liquor, 5150 other vegetal material and residues, 5160 charcoal). Every observation carries the
attribute CONVERSION_FACTOR (UNSD's own NCV for that country, commodity, transaction and year).
The raw responses are written unchanged to sdmx/<CC>_2015_2022.xml with a receipt (url, UTC time, HTTP status, headers, final url, bytes,
SHA256); a re-run refuses to overwrite an existing response (the first retrieval is the record).
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

G3 = Path(__file__).resolve().parents[1]
OUT = G3 / "sdmx"
AREAS = {"TH": "764", "PH": "608", "SG": "702"}
COMMODITIES = ["0100", "0110", "0121", "0129", "0200", "0210", "0220", "0311", "4694", "5110", "5120", "5140", "5150", "5160"]
URL = "https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY,/A.{area}.{com}./?startPeriod=2015&endPeriod=2022"


def main():
    OUT.mkdir(exist_ok=True)
    for cc, area in AREAS.items():
        f = OUT / f"{cc}_2015_2022.xml"
        if f.exists():
            print(f"{f.name}: exists, not re-downloaded")
            continue
        url = URL.format(area=area, com="+".join(COMMODITIES))
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.sdmx.genericdata+xml;version=2.1", "User-Agent": "research-script"})
        t = datetime.now(timezone.utc).isoformat()
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read(); status = r.status; final = r.geturl(); headers = dict(r.headers.items())
        f.write_bytes(body)
        rec = dict(file=f.name, url=url, utc=t, http_status=status, headers=headers, final_url=final, bytes=len(body),
                   sha256=hashlib.sha256(body).hexdigest(), status="RETRIEVED")
        (OUT / f"{f.name}.receipt.json").write_text(json.dumps(rec, indent=2) + "\n")
        print(f.name, status, len(body), rec["sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
