"""G4 (V4 W07, section B-G4): UNSD SDMX queries allowed by instruction A5 (same public interface as the repository
research_inputs/assembly_v1/sources/unsd_targeted/, no login). One request per country: coal and biomass commodities, all transactions,
2015-2022. Raw responses are saved unchanged with a receipt (url, UTC time, HTTP status, final url, bytes, SHA256).

    C:/Users/20122/miniconda3/python.exe -I scripts/g4_sdmx.py        (Windows python; writes under G4/sdmx only)
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "sdmx"
AREAS = {"LA": "418", "MM": "104", "KH": "116", "BN": "096"}
COMS = ["0100", "0110", "0121", "0129", "0200", "0210", "0220", "5110", "5120", "5140", "5150", "5160"]
BASE = "https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY,/A.{area}.{coms}./?startPeriod=2015&endPeriod=2022"


def main():
    OUT.mkdir(exist_ok=True)
    for cc, area in AREAS.items():
        url = BASE.format(area=area, coms="+".join(COMS))
        req = urllib.request.Request(url, headers={"User-Agent": "research-script/1.0", "Accept": "application/vnd.sdmx.genericdata+xml;version=2.1"})
        t = dt.datetime.now(dt.timezone.utc).isoformat()
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read(); status = r.status; final = r.geturl(); hdr = dict(r.headers)
        except Exception as e:   # recorded, not retried in a loop
            body = b""; status = getattr(e, "code", None); final = url; hdr = {"error": repr(e)}
        f = OUT / f"{cc}_coal_biomass_2015_2022.xml"
        f.write_bytes(body)
        rec = dict(file=f.name, url=url, utc=t, http_status=status, final_url=final, bytes=len(body),
                   sha256=hashlib.sha256(body).hexdigest(), headers={k: v for k, v in hdr.items() if k.lower() in ("content-type", "date", "error")})
        (OUT / f"{f.name}.receipt.json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
        print(cc, status, len(body), rec["sha256"][:16])
        time.sleep(2)


if __name__ == "__main__":
    sys.exit(main())
