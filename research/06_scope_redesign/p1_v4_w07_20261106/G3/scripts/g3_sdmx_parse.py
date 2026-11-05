"""G3: parse the SDMX responses of g3_sdmx.py into one tidy table and derive UNSD's own 2019 NCV per country x commodity.

    python scripts/g3_sdmx_parse.py

Output tables/SDMX_OBS_TH_PH_SG.csv (cc, commodity, transaction, year, value, unit, unit_mult, obs_status, conversion_factor, other attributes)
and tables/SDMX_NCV_2019.csv (per cc x commodity: distinct 2019 conversion factors and the transactions that carry them). Codes are named
with codelists.json of the repository (research_inputs/assembly_v1/sources/unsd_targeted/, read only).
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

G3 = Path(__file__).resolve().parents[1]
REPO = Path("/home/jin/wt_v4_g3")
NS = {"g": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic", "m": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"}


def parse(p: Path, cc: str, codes: dict) -> list[dict]:
    root = ET.parse(p).getroot()
    rows = []
    for s in root.iter(f"{{{NS['g']}}}Series"):
        key = {v.get("id"): v.get("value") for v in s.find("g:SeriesKey", NS)}
        satt = {v.get("id"): v.get("value") for v in (s.find("g:Attributes", NS) or [])}
        for o in s.findall("g:Obs", NS):
            y = o.find("g:ObsDimension", NS).get("value"); v = o.find("g:ObsValue", NS).get("value")
            oatt = {a.get("id"): a.get("value") for a in (o.find("g:Attributes", NS) or [])}
            rows.append(dict(cc=cc, commodity_code=key["COMMODITY"], commodity=codes["CL_COMMODITY_NRG"].get(key["COMMODITY"], ""),
                             transaction_code=key["TRANSACTION"], transaction=codes["CL_TRANSACTION_NRG"].get(key["TRANSACTION"], ""),
                             year=int(y), value=float(v), unit=satt.get("UNIT_MEASURE", ""), unit_mult=oatt.get("UNIT_MULT", ""),
                             obs_status=oatt.get("OBS_STATUS", ""), conversion_factor=(float(oatt["CONVERSION_FACTOR"]) if "CONVERSION_FACTOR" in oatt else None),
                             other_attributes=json.dumps({k: x for k, x in oatt.items() if k not in ("UNIT_MULT", "OBS_STATUS", "CONVERSION_FACTOR")})))
    return rows


def main():
    codes = json.loads((REPO / "research_inputs/assembly_v1/sources/unsd_targeted/codelists.json").read_text())
    rows = []
    for cc in ("TH", "PH", "SG"):
        rows += parse(G3 / "sdmx" / f"{cc}_2015_2022.xml", cc, codes)
    D = pd.DataFrame(rows).sort_values(["cc", "commodity_code", "transaction_code", "year"])
    D.to_csv(G3 / "tables/SDMX_OBS_TH_PH_SG.csv", index=False)
    z = D[(D.year == 2019) & D.conversion_factor.notna()]
    out = []
    for (cc, code, com), g in z.groupby(["cc", "commodity_code", "commodity"]):
        for cf, h in g.groupby("conversion_factor"):
            out.append(dict(cc=cc, commodity_code=code, commodity=com, conversion_factor=cf, n_obs=len(h), unit=";".join(sorted(h.unit.unique())),
                            transactions=";".join(f"{t}:{n}" for t, n in zip(h.transaction_code, h.transaction))[:600]))
    N = pd.DataFrame(out)
    N.to_csv(G3 / "tables/SDMX_NCV_2019.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 120)
    print(len(D), "observations;", D.groupby("cc").size().to_dict())
    print(N.drop(columns="transactions").to_string())
    print(N[["cc", "commodity", "conversion_factor", "transactions"]].to_string())


if __name__ == "__main__":
    main()
