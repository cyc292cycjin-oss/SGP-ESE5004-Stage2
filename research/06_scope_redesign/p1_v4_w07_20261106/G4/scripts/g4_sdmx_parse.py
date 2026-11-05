"""G4: parse the saved SDMX responses (sdmx/*.xml) into a flat table and the conversion factors per country / commodity / transaction / year.

    /home/jin/miniforge3/envs/pypsa-earth/bin/python -I scripts/g4_sdmx_parse.py   (WSL)
Outputs evidence/SDMX_COAL_BIOMASS_2015_2022.csv, evidence/SDMX_CONVERSION_FACTORS.csv (distinct factors per country / commodity / year).
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

G4 = Path(__file__).resolve().parents[1]
NS = {"g": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"}
COM = {"0100": "Hard coal", "0110": "Anthracite", "0121": "Coking coal", "0129": "Other bituminous coal", "0200": "Brown coal", "0210": "Sub-bituminous coal",
       "0220": "Lignite", "5110": "Fuelwood", "5120": "Bagasse", "5140": "Black liquor", "5150": "Other vegetal material and residues", "5160": "Charcoal"}


def main():
    cl = json.loads((Path("/home/jin/wt_v4_g4/research_inputs/assembly_v1/sources/unsd_targeted/codelists.json")).read_text()) if len(sys.argv) < 2 else json.loads(Path(sys.argv[1]).read_text())
    tr_names = cl["CL_TRANSACTION_NRG"]
    rows = []
    for f in sorted((G4 / "sdmx").glob("*_coal_biomass_2015_2022.xml")):
        cc = f.name[:2]
        root = ET.parse(f).getroot()
        for s in root.iter(f"{{{NS['g']}}}Series"):
            key = {v.get("id"): v.get("value") for v in s.find("g:SeriesKey", NS)}
            sat = {v.get("id"): v.get("value") for v in s.find("g:Attributes", NS)} if s.find("g:Attributes", NS) is not None else {}
            for o in s.findall("g:Obs", NS):
                y = o.find("g:ObsDimension", NS).get("value"); val = o.find("g:ObsValue", NS)
                at = {v.get("id"): v.get("value") for v in o.find("g:Attributes", NS)} if o.find("g:Attributes", NS) is not None else {}
                rows.append(dict(iso=cc, commodity_code=key["COMMODITY"], commodity=COM.get(key["COMMODITY"], key["COMMODITY"]), transaction_code=key["TRANSACTION"],
                                 transaction=str(tr_names.get(key["TRANSACTION"], key["TRANSACTION"])), year=int(y), value=float(val.get("value")) if val is not None else None,
                                 unit=sat.get("UNIT_MEASURE", ""), unit_mult=at.get("UNIT_MULT", ""), obs_status=at.get("OBS_STATUS", ""),
                                 conversion_factor=float(at["CONVERSION_FACTOR"]) if "CONVERSION_FACTOR" in at else None, comment=at.get("OBS_COMMENT", ""),
                                 source_file=f.name))
    d = pd.DataFrame(rows).sort_values(["iso", "commodity_code", "transaction_code", "year"])
    d.to_csv(G4 / "evidence/SDMX_COAL_BIOMASS_2015_2022.csv", index=False)
    cf = (d.dropna(subset=["conversion_factor"]).groupby(["iso", "commodity_code", "commodity", "year", "conversion_factor"])
          .agg(n_transactions=("transaction_code", "nunique"), transactions=("transaction_code", lambda s: "+".join(sorted(set(s))))).reset_index())
    cf.to_csv(G4 / "evidence/SDMX_CONVERSION_FACTORS.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500); pd.set_option("display.max_colwidth", 60)
    print(len(d), "observations;", d.groupby("iso").size().to_dict())
    print(cf[cf.year.isin([2018, 2019, 2020])].to_string(index=False))
    print(d[d.year == 2019].groupby(["iso", "obs_status"]).size())


if __name__ == "__main__":
    main()
