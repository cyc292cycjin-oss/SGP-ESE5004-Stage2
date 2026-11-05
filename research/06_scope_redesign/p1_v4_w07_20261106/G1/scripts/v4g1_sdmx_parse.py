"""V4 W07 G1: parse the stored UNSD SDMX responses (G1/sdmx/*.xml) into a flat table: commodity, transaction (codes and labels from the
repository codelists.json), year, value, unit, unit multiplier, OBS_STATUS, CONVERSION_FACTOR. Output sdmx/MY_SDMX_OBS.csv.
"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

G1 = Path(__file__).resolve().parents[1]
CL = Path("/home/jin/wt_v4_g1/research_inputs/assembly_v1/sources/unsd_targeted/codelists.json")
NS = {"g": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"}


def parse(p: Path) -> pd.DataFrame:
    root = ET.parse(p).getroot(); rows = []
    for s in root.iter("{%s}Series" % NS["g"]):
        key = {v.get("id"): v.get("value") for v in s.find("g:SeriesKey", NS)}
        att = {v.get("id"): v.get("value") for v in (s.find("g:Attributes", NS) or [])}
        for o in s.findall("g:Obs", NS):
            oa = {v.get("id"): v.get("value") for v in (o.find("g:Attributes", NS) or [])}
            rows.append(dict(file=p.name, commodity_code=key.get("COMMODITY"), transaction_code=key.get("TRANSACTION"), year=int(o.find("g:ObsDimension", NS).get("value")),
                             value=float(o.find("g:ObsValue", NS).get("value")), unit=att.get("UNIT_MEASURE"), unit_mult=oa.get("UNIT_MULT"), obs_status=oa.get("OBS_STATUS"),
                             conversion_factor=float(oa["CONVERSION_FACTOR"]) if oa.get("CONVERSION_FACTOR") else None))
    return pd.DataFrame(rows)


def main():
    cl = json.loads(CL.read_text())
    D = pd.concat([parse(p) for p in sorted((G1 / "sdmx").glob("*.xml"))], ignore_index=True)
    D["commodity"] = D.commodity_code.map(cl["CL_COMMODITY_NRG"]); D["transaction"] = D.transaction_code.map(cl["CL_TRANSACTION_NRG"])
    D["obs_status_label"] = D.obs_status.map(cl["CL_OBS_STATUS"])
    D = D.drop_duplicates(subset=["commodity_code", "transaction_code", "year", "value", "conversion_factor"]).sort_values(["commodity_code", "transaction_code", "year"])
    D.to_csv(G1 / "sdmx/MY_SDMX_OBS.csv", index=False, float_format="%.12g")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 70)
    coal = D[D.commodity_code.isin(["0100", "0110", "0121", "0129", "0200", "0210", "0220", "0311", "0350"])]
    print(coal[coal.year == 2019][["commodity", "transaction", "value", "unit", "obs_status", "conversion_factor"]].to_string())
    print(coal.groupby(["commodity", "year"]).conversion_factor.agg(["min", "max", "count"]).to_string())
    bio = D[D.commodity_code.isin(["5110", "5120", "5140", "5150", "5160"])]
    print(bio[bio.year == 2019][["commodity", "transaction", "value", "unit", "obs_status", "conversion_factor"]].to_string())
    cf = D[D.year == 2019].groupby("commodity").conversion_factor.agg(["min", "max", "count"])
    print(cf.to_string())


if __name__ == "__main__":
    main()
