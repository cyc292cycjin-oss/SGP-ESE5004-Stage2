"""W12-4: UNSD SDMX query, 11 ASEAN countries, year 2019, ALL commodities and ALL transactions (the only download instruction A5 allows).

    PYTHONHASHSEED=0 python scripts/w12_sdmx.py            (WSL pypsa-earth python; network access to data.un.org)

Same public interface as research_inputs/assembly_v1/sources/unsd_targeted/ (no login): dataflow UNSD,DF_UNDATA_ENERGY, key
A.<area>..  (commodity and transaction wildcards), startPeriod = endPeriod = 2019. The raw responses are written unchanged to
sdmx/<CC>_2019_all.xml with a receipt (url, UTC time, HTTP status, headers, final url, bytes, SHA256); a re-run refuses to overwrite an
existing response (the first retrieval is the record). Purpose: identify which commodities / flows the UNdata web export used by the model
(pypsa-asean data/demand/unsd/data, 52 files) lacks, against UNSD's own database of the same year.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

W12 = Path(__file__).resolve().parents[1]
OUT = W12 / "sdmx"
AREAS = {"BN": "096", "KH": "116", "ID": "360", "LA": "418", "MY": "458", "MM": "104", "PH": "608", "SG": "702", "TH": "764", "TL": "626", "VN": "704"}
URL = "https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY,/A.{area}../?startPeriod=2019&endPeriod=2019"


def main(only: list[str]):
    OUT.mkdir(exist_ok=True)
    for cc, area in AREAS.items():
        if only and cc not in only:
            continue
        f = OUT / f"{cc}_2019_all.xml"
        if f.exists():
            print(f"{f.name}: exists, not re-downloaded")
            continue
        url = URL.format(area=area)
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.sdmx.genericdata+xml;version=2.1", "User-Agent": "research-script"})
        t = datetime.now(timezone.utc).isoformat()
        for k in range(3):
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    body = r.read(); status = r.status; final = r.geturl(); headers = dict(r.headers.items())
                break
            except Exception as exc:   # noqa: BLE001  (retry twice, then report)
                print(cc, "attempt", k + 1, "failed:", exc)
                time.sleep(20)
        else:
            print(cc, "NOT RETRIEVED"); continue
        f.write_bytes(body)
        rec = dict(file=f.name, url=url, utc=t, http_status=status, headers=headers, final_url=final, bytes=len(body),
                   sha256=hashlib.sha256(body).hexdigest(), status="RETRIEVED")
        (OUT / f"{f.name}.receipt.json").write_text(json.dumps(rec, indent=2) + "\n")
        print(f.name, status, len(body), rec["sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
