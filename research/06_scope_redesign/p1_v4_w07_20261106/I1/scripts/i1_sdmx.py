"""I1-1a: UNSD SDMX 2019 responses (W12 retrieval, 11 ASEAN countries, all commodities / transactions) -> integrity check, observation
table, capsule-format records for the base reconstruction, and the conversion-factor (NCV) comparison.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i1_sdmx.py

A. Integrity: SHA256 of every W12 response against its receipt and DATA_REGISTRY_W12_SDMX.csv; XML well formed (GenericData, Header,
   DataSet, no Footer / error message); every observation is 2019; series and observation counts; the main final-consumption series
   (12 / 121 / 1231 / 1221 per carrier group) present for every country with UNdata export rows.
B. Observations: one row per (country, commodity, transaction) with the raw value string, unit, UNIT_MULT, OBS_STATUS, CONVERSION_FACTOR.
C. Capsule records: the same fields as research_inputs/assembly_v1/sources/UNSD_2019_SOURCE_CAPSULE.json (export naming of commodities,
   units in the export's thousand t / TJ / million kWh / thousand m3; quantity rescaled exactly with Decimal), plus CommodityCode,
   TransactionCode, CONVERSION_FACTOR and OBS_STATUS. Memo items 'Of which: biogasoline / biodiesel / bio jet kerosene' are kept apart
   (blend memo table). Generation-by-source commodities (7000G ...), capacities (EC, unit MW), refinery output (GR) are not end-use
   energy and are left out (listed).
D. NCV comparison: SDMX CONVERSION_FACTOR per country x commodity (all consumption flows; min / max when they differ) against the v3
   frozen upstream factors, W11 (b) UNSD 2019 values derived from the UN Energy Balances 2019 publication, decision 207 values and the
   W07 country-session proposals (decision 208 item 2 list as given in G0-G4).
No download; nothing in the repository is written.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from decimal import Decimal as D
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i1_common as cm  # noqa: E402

NS = {"g": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic", "m": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"}
# SDMX commodity code -> commodity name as written in the UNdata export / frozen upstream dictionary (case is normalised by the
# reconstruction's commodity(); only true spelling differences matter)
SDMX_TO_EXPORT = {
    "0100": "Hard coal", "0110": "Anthracite", "0121": "Coking coal", "0129": "Other bituminous coal", "0200": "Brown coal",
    "0210": "Sub-bituminous coal", "0220": "Lignite", "0311": "Coke-oven coke", "0312": "Gas coke", "0320": "Patent fuel",
    "0330": "Brown coal briquettes", "0340": "Coal Tar", "0350": "Coke Oven Gas", "0360": "Gasworks Gas", "0371": "Blast Furnace Gas",
    "0379": "Other recovered gases", "0390": "Other coal products", "1100": "Peat", "1200": "Peat products", "2000": "Oil shale",
    "3000": "Natural gas (including LNG)", "4100": "Conventional crude oil", "4200": "Natural gas liquids", "4300": "Refinery feedstocks",
    "4400": "Additives and Oxygenates", "4500": "Other hydrocarbons", "4610": "Refinery gas", "4620": "Ethane",
    "4630": "Liquefied petroleum gas (LPG)", "4640": "Naphtha", "4651": "Aviation gasoline", "4652": "Motor Gasoline",
    "4653": "Gasoline-type jet fuel", "4661": "Kerosene-type Jet Fuel", "4669": "Other kerosene", "4670": "Gas Oil/ Diesel Oil",
    "4680": "Fuel oil", "4691": "White spirit and special boiling point industrial spirits", "4692": "Lubricants", "4693": "Paraffin waxes",
    "4694": "Petroleum coke", "4695": "Bitumen", "4699": "Other oil products n.e.c.", "5110": "Fuelwood", "5120": "Bagasse",
    "5130": "Animal waste", "5140": "Black Liquor", "5150": "Other Vegetal Material and Residues", "5160": "Charcoal", "5210": "Biogasoline",
    "5220": "Biodiesel", "5230": "Bio jet kerosene", "5290": "Other liquid biofuels", "5300": "Biogases", "6100": "Industrial Waste",
    "6200": "Municipal Wastes", "7000": "Electricity", "8000": "Heat", "DG": "Direct use of geothermal heat", "DS": "Direct use of solar thermal heat"}
MEMO = {"5212": ("Biogasoline", "Motor Gasoline"), "5222": ("Biodiesel", "Gas Oil/ Diesel Oil"), "5232": ("Bio jet kerosene", "Kerosene-type Jet Fuel")}
NOT_END_USE = {"7000G", "7000H", "7000N", "7000O", "7000S", "7000T", "7000W", "8000T", "9101", "EC", "GR", "WF"}
UNIT = {"TN": ("Metric tons,  thousand", 3), "TJ": ("Terajoules", 0), "GWHR": ("Kilowatt-hours, million", 0), "M3": ("Cubic metres, thousand", 3),
        "MW": ("Kilowatts,  thousand", 3)}
# decision 207 / W07 country-session coal NCVs (GJ/t) as given in the W07 reports (G0 section 0 item 3, G1 item 3, G2 item 7, G3 item 3,
# G4 item 3) and W11 (b) (UN Energy Balances 2019 publication / export): used only for the comparison table
DECISION_NCV = {
    ("ID", "Hard coal"): dict(d207=20.29, w11_b=24.480, session="G0 main 20.29 (decision 207 item 2); UNSD 24.48 / IPCC 18.9 sensitivities"),
    ("VN", "Hard coal"): dict(d207=23.446, w11_b=23.446, session="G2 main 23.446 (SDMX 2007-2022)"),
    ("MM", "Hard coal"): dict(d207=23.26, w11_b=23.260, session="G4 main 23.26; IPCC 18.9 sensitivity"),
    ("PH", "Brown coal"): dict(d207=22.058, w11_b=22.064, session="G3 main 22.058 (SDMX)"),
    ("KH", "Brown coal"): dict(d207=19.853, w11_b=19.878, session="G4 main 19.853 (SDMX parent)"),
    ("MY", "Hard coal"): dict(d207=26.394, w11_b=None, session="G1 main 26.394 (SDMX)"),
    ("TH", "Hard coal"): dict(d207=26.377, w11_b=None, session="G3 main SDMX parent 26.377"),
    ("TH", "Brown coal"): dict(d207=10.547, w11_b=None, session="G3 main SDMX parent 10.547 (children 18.9 / 11.9 sensitivities)"),
    ("LA", "Hard coal"): dict(d207=25.121, w11_b=25.12, session="G4 main 25.121 (SDMX)"),
    ("LA", "Brown coal"): dict(d207=9.63, w11_b=9.63, session="G4 main 9.63 (SDMX)"),
    ("SG", "Hard coal"): dict(d207=25.8, w11_b=25.8, session="G3 unchanged 25.8"),
    ("BN", "Brown coal"): dict(d207=18.841, w11_b=None, session="G4 SDMX parent 18.841 (autoproducer transformation only)"),
}
FINAL_TX = {"12", "121", "1211", "1213", "1214", "1214A", "1214B", "1214C", "1214D", "1214E", "1214F", "1214G", "1214H", "1214I", "1214J", "1214O",
            "122", "1221", "1222", "1223", "1224", "1225", "1226", "123", "1231", "1232", "1234", "1235", "11", "051", "052"}


def integrity(ev: cm.Evidence) -> pd.DataFrame:
    reg = pd.read_csv(cm.W12 / "DATA_REGISTRY_W12_SDMX.csv").set_index("path")
    rows = []
    for cc in cm.ASEAN:
        p = cm.SDMX_DIR / f"{cc}_2019_all.xml"
        rec = json.loads((cm.SDMX_DIR / f"{cc}_2019_all.xml.receipt.json").read_text())
        sha = cm.sha256(p)
        root = ET.parse(p).getroot()
        hdr = root.find("m:Header", NS)
        prepared = hdr.find("m:Prepared", NS).text if hdr is not None and hdr.find("m:Prepared", NS) is not None else ""
        footer = [e for e in root.iter() if e.tag.endswith("Footer") or e.tag.endswith("ErrorMessage")]
        series = list(root.iter(f"{{{NS['g']}}}Series"))
        years = set(); nobs = 0
        for s in series:
            for o in s.findall("g:Obs", NS):
                years.add(o.find("g:ObsDimension", NS).get("value")); nobs += 1
        r = dict(country=cc, file=f"sdmx/{p.name}", bytes=p.stat().st_size, sha256=sha, sha256_receipt=rec["sha256"],
                 sha256_registry=reg.loc[f"sdmx/{p.name}", "sha256"], sha_ok=(sha == rec["sha256"] == reg.loc[f"sdmx/{p.name}", "sha256"]),
                 bytes_ok=(p.stat().st_size == rec["bytes"]), http_status=rec["http_status"], retrieved_utc=rec["utc"], prepared=prepared,
                 root=root.tag.split("}")[1], footer_or_error=len(footer), series=len(series), observations=nobs, years=";".join(sorted(years)),
                 url=rec["url"], final_url=rec["final_url"])
        rows.append(r)
        ev.add(f"raw.{cc}.sha256", sha, "sha256", "VERIFIED", "A", f"W12 sdmx/{p.name}", f"receipt + W12 registry equal: {r['sha_ok']}; retrieved {rec['utc']}")
        ev.add(f"raw.{cc}.observations", nobs, "count", "VERIFIED", "A", f"W12 sdmx/{p.name}", f"{len(series)} series, years {r['years']}, footer/error elements {len(footer)}")
    T = pd.DataFrame(rows)
    cm.write_csv(T.to_dict("records"), cm.BASE_OUT / "SDMX_RAW_RESPONSES.csv")
    if not (T.sha_ok.all() and T.bytes_ok.all() and (T.footer_or_error == 0).all() and (T.years == "2019").all()):
        raise SystemExit("STOP: an SDMX raw response fails the integrity check")
    return T


def parse(codes: dict) -> pd.DataFrame:
    rows = []
    for cc in cm.ASEAN:
        p = cm.SDMX_DIR / f"{cc}_2019_all.xml"
        root = ET.parse(p).getroot()
        for s in root.iter(f"{{{NS['g']}}}Series"):
            key = {v.get("id"): v.get("value") for v in s.find("g:SeriesKey", NS)}
            sa = s.find("g:Attributes", NS)
            satt = {v.get("id"): v.get("value") for v in (sa if sa is not None else [])}
            for o in s.findall("g:Obs", NS):
                oa = o.find("g:Attributes", NS)
                oatt = {a.get("id"): a.get("value") for a in (oa if oa is not None else [])}
                att = {**satt, **oatt}
                rows.append(dict(country=cc, area=key["REF_AREA"], commodity_code=key["COMMODITY"],
                                 commodity_sdmx=codes["CL_COMMODITY_NRG"].get(key["COMMODITY"], ""), transaction_code=key["TRANSACTION"],
                                 transaction_sdmx=codes["CL_TRANSACTION_NRG"].get(key["TRANSACTION"], ""), value_raw=o.find("g:ObsValue", NS).get("value"),
                                 unit=att.get("UNIT_MEASURE", ""), unit_mult=att.get("UNIT_MULT", "0"), obs_status=att.get("OBS_STATUS", ""),
                                 conversion_factor=att.get("CONVERSION_FACTOR", ""), source_file=f"sdmx/{p.name}"))
    return pd.DataFrame(rows)


def capsule(O: pd.DataFrame, shas: dict) -> tuple[list, list, list]:
    recs, memo, dropped = [], [], []
    for r in O.itertuples():
        if r.commodity_code in MEMO:
            memo.append(dict(country=r.country, memo_code=r.commodity_code, bio=MEMO[r.commodity_code][0], petroleum=MEMO[r.commodity_code][1],
                             transaction_code=r.transaction_code, transaction=r.transaction_sdmx, value_raw=r.value_raw, unit=r.unit, unit_mult=r.unit_mult,
                             obs_status=r.obs_status, source_file=r.source_file))
            continue
        if r.commodity_code in NOT_END_USE or r.commodity_code not in SDMX_TO_EXPORT or r.unit not in UNIT:
            dropped.append(dict(country=r.country, commodity_code=r.commodity_code, commodity=r.commodity_sdmx, transaction_code=r.transaction_code,
                                transaction=r.transaction_sdmx, unit=r.unit, reason="generation / capacity / refinery output item, not end-use energy"
                                if r.commodity_code in NOT_END_USE else "commodity or unit outside the capsule mapping"))
            continue
        uname, scale = UNIT[r.unit]
        q = D(r.value_raw) * (D(10) ** (int(r.unit_mult) - scale))
        com = SDMX_TO_EXPORT[r.commodity_code]
        recs.append({"Country or Area": cm.CC_NAME[r.country], "Commodity - Transaction": f"{com} - {r.transaction_sdmx}", "Year": "2019", "Unit": uname,
                     "Quantity": format(q.normalize(), "f") if q != 0 else "0", "Quantity Footnotes": r.obs_status, "Country": r.country, "Commodity": com,
                     "Transaction": r.transaction_sdmx, "SourceFile": r.source_file, "SourceSHA256": shas[r.country],
                     "PhysicalLine": f"{r.commodity_code}:{r.transaction_code}", "CommodityCode": r.commodity_code, "TransactionCode": r.transaction_code,
                     "CONVERSION_FACTOR": r.conversion_factor, "OBS_STATUS": r.obs_status})
    return recs, memo, dropped


def ncv_table(O: pd.DataFrame, ev: cm.Evidence) -> pd.DataFrame:
    fz = json.loads((cm.SRC / "FROZEN_UPSTREAM_CONVERSIONS.json").read_text())["constants"]["fuels_conv_toTWh"]
    fzl = {k.lower(): v for k, v in fz.items()}
    rows = []
    X = O[(O.conversion_factor != "") & O.unit.isin(["TN", "M3"]) & O.transaction_code.isin(FINAL_TX | {"08", "088", "08811", "08812", "08821", "08822", "01", "03"})].copy()
    X["cf"] = X.conversion_factor.astype(float)
    for (cc, code), g in X.groupby(["country", "commodity_code"]):
        com = SDMX_TO_EXPORT.get(code, g.commodity_sdmx.iloc[0])
        cons = g[g.transaction_code.isin(FINAL_TX)]
        use = cons if len(cons) else g
        v3 = fzl.get(com.lower())
        v3_gj = v3 * 1e6 * 3.6 / 1e3 if v3 is not None else None   # TWh per kt (per 1000 m3) x 1e6 MWh/TWh x 3.6 GJ/MWh / 1e3 t = GJ per t (per m3)
        dec = DECISION_NCV.get((cc, com), {})
        cf_min, cf_max = float(use.cf.min()), float(use.cf.max())
        rows.append(dict(country=cc, commodity_code=code, commodity=com, unit_basis="GJ per m3" if g.unit.iloc[0] == "M3" else "GJ per t",
                         sdmx_cf_consumption_min=cf_min, sdmx_cf_consumption_max=cf_max, n_consumption_obs=int(len(cons)),
                         sdmx_cf_all_flows=";".join(f"{t}:{c:g}" for t, c in sorted(set(zip(g.transaction_code, g.cf)))),
                         v3_frozen=v3_gj, sdmx_vs_v3_pct=((cf_min / v3_gj - 1) * 100) if v3_gj else None,
                         w11_b_unsd2019_publication=dec.get("w11_b"), decision_207_or_session_main=dec.get("d207"),
                         sdmx_vs_decision_pct=((cf_min / dec["d207"] - 1) * 100) if dec.get("d207") else None, session_note=dec.get("session", "")))
    T = pd.DataFrame(rows).sort_values(["country", "commodity_code"])
    cm.write_csv(T.to_dict("records"), cm.BASE_OUT / "SDMX_NCV_COMPARISON.csv")
    for r in T[T.commodity.isin(["Hard coal", "Brown coal", "Sub-bituminous coal", "Lignite", "Other bituminous coal", "Anthracite", "Coking coal"])].itertuples():
        ev.add(f"ncv.{r.country}.{r.commodity_code}", dict(sdmx_min=r.sdmx_cf_consumption_min, sdmx_max=r.sdmx_cf_consumption_max, v3=r.v3_frozen,
                                                           w11_b=r.w11_b_unsd2019_publication, decision=r.decision_207_or_session_main), "GJ/t", "VERIFIED", "A",
               f"sdmx/{r.country}_2019_all.xml CONVERSION_FACTOR", f"{r.commodity}; flows {r.sdmx_cf_all_flows}")
    return T


def main():
    ev = cm.Evidence("I1_1a_sdmx")
    T = integrity(ev)
    codes = json.loads((cm.SRC / "unsd_targeted/codelists.json").read_text())
    O = parse(codes)
    cm.write_csv(O.to_dict("records"), cm.BASE_OUT / "SDMX_2019_OBSERVATIONS.csv")
    shas = dict(zip(T.country, T.sha256))
    recs, memo, dropped = capsule(O, shas)
    cm.write_json(dict(schema="i1-sdmx-capsule-1", year=2019, source="UNSD SDMX DF_UNDATA_ENERGY v1.2, W12 retrieval 2026-11-05T19:44-19:45 UTC",
                       files={f"sdmx/{cc}_2019_all.xml": shas[cc] for cc in cm.ASEAN}, records=recs), cm.SCRATCH / "SDMX_2019_CAPSULE.json")
    cm.write_csv(recs, cm.BASE_OUT / "SDMX_2019_CAPSULE_RECORDS.csv")
    cm.write_csv(memo, cm.BASE_OUT / "SDMX_2019_BLEND_MEMO.csv")
    cm.write_csv(dropped, cm.BASE_OUT / "SDMX_2019_NOT_END_USE.csv")
    N = ncv_table(O, ev)
    ev.add("capsule.records", len(recs), "count", "EXACT", "A", "BASE2019_SDMX/SDMX_2019_CAPSULE_RECORDS.csv", f"memo rows {len(memo)}, left out {len(dropped)}")
    p = ev.write()
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 300)
    print(T[["country", "bytes", "sha_ok", "series", "observations", "years", "prepared", "footer_or_error"]].to_string())
    print("capsule records", len(recs), "memo", len(memo), "dropped", len(dropped))
    print(pd.DataFrame(memo).to_string() if memo else "no blend memo rows")
    coal = N[N.commodity.str.contains("coal|Lignite|coke|Anthracite", case=False)]
    print(coal[["country", "commodity", "sdmx_cf_consumption_min", "sdmx_cf_consumption_max", "v3_frozen", "w11_b_unsd2019_publication", "decision_207_or_session_main", "sdmx_cf_all_flows"]].to_string())
    oth = N[~N.index.isin(coal.index)]
    print(oth[["country", "commodity", "sdmx_cf_consumption_min", "sdmx_cf_consumption_max", "v3_frozen", "sdmx_vs_v3_pct"]].round(4).to_string())
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
