"""W12-4: coverage gaps of the UNdata web export (pypsa-asean data/demand/unsd/data, 52 files, retrieved 2025-05-02) that feeds the 2019
demand base (reconstruct_base_accounts.py), per country x sector x fuel group.

A. Truncation scan: data rows per export file; files with exactly 100,000 data rows hit the web-export limit; the ASEAN countries after
   the cut (alphabetical order) are missing from that file.
B. UN Energy Balances 2019 (W11 ncv/UNSD_EXPORT_VS_EB2019_BY_FLOW.csv, publication TJ vs export x upstream factors) -> gap per country x
   flow x group, with a vintage flag (natural gas: publication / (export TJ) = 0.900 when the publication and the export are the same
   data vintage, because the export gas TJ is GCV and the balance NCV).
C. UNSD SDMX 2019, all commodities and transactions (sdmx/<CC>_2019_all.xml of scripts/w12_sdmx.py): every (commodity, transaction) pair
   with a value that the export lacks; commodity names mapped to the upstream fuel dictionary (FROZEN_UPSTREAM_CONVERSIONS.json) to say
   whether the 2019 base would have used it.
D. Model scale: missing 2019 MWh mapped to the D1 accounts and x the ATS-table multiplier of the same country / account / carrier
   (reading I, multiplier unchanged); under the ATS anchor (reading II) sector totals stay at the AEO8 anchors and only shares move.
Writes tables/W12_4_*.csv and evidence/W12_4.json. Nothing is solved; nothing in the repository is written.
"""
from __future__ import annotations

import glob
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w12_common as cm  # noqa: E402

NS = {"g": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"}
SDMX = cm.W12 / "sdmx"
ORDER = ["Brunei Darussalam", "Cambodia", "Indonesia", "Lao People's Dem. Rep.", "Malaysia", "Myanmar", "Philippines", "Singapore", "Thailand",
         "Timor-Leste", "Viet Nam"]
SECTOR_TX = {   # SDMX / export transaction (normalised) -> (model sector, D1 account)
    "consumption by households": ("Residential", "ResidentialFuel"),
    "consumption by commerce and public services": ("Commercial", "ServicesFuel"),
    "consumption by commercial and public services": ("Commercial", "ServicesFuel"),
    "consumption by agriculture, forestry and fishing": ("AgricultureOthers", "AgricultureFinalEnergy"),
    "consumption in agriculture, forestry and fishing": ("AgricultureOthers", "AgricultureFinalEnergy"),
    "consumption by manufacturing, construction and non-fuel mining industry": ("Industry", "IndustryFinalEnergy"),
    "consumption by manufacturing, construction and non-fuel industry": ("Industry", "IndustryFinalEnergy"),
    "consumption in road": ("Transport", "RoadResidualFuel"), "consumption by road": ("Transport", "RoadResidualFuel"),
    "consumption in rail": ("Transport", "RailNonElectric"), "consumption by rail": ("Transport", "RailNonElectric"),
    "consumption in domestic aviation": ("Transport", "DomesticAviationFuel"), "consumption by domestic aviation": ("Transport", "DomesticAviationFuel"),
    "consumption in domestic navigation": ("Transport", "DomesticShippingFuel"), "consumption by domestic navigation": ("Transport", "DomesticShippingFuel"),
    "consumption not elsewhere specified (transport)": ("Transport", "TransportNEC"),
    "consumption not elsewhere specified (other)": ("Other", "OtherNEC"), "consumption by other consumers not elsewhere specified": ("Other", "OtherNEC"),
    "international marine bunkers": ("InternationalBunkers", "InternationalShippingBunker"),
    "international aviation bunkers": ("InternationalBunkers", "InternationalAviationBunker"),
    "non-energy uses": ("NonEnergyUse", "NonEnergy"), "consumption for non-energy uses": ("NonEnergyUse", "NonEnergy"),
}


def norm(x: str) -> str:
    x = re.sub(r"\s+", " ", str(x).strip().lower())
    return {"hrad coal": "hard coal", "liquified petroleum gas (lpg)": "liquefied petroleum gas (lpg)", "liquified petroleum gas": "liquefied petroleum gas (lpg)",
            "coke-oven coke": "coke oven coke", "natural gas": "natural gas (including lng)", "total electricity": "electricity"}.get(x, x)


def truncation_scan(ev: cm.Evidence) -> pd.DataFrame:
    rows = []
    for f in sorted(glob.glob(str(cm.UNSD_DIR / "UNdata_Export_*.txt"))):
        lines = Path(f).read_text(encoding="utf-8", errors="replace").splitlines()
        data = []
        for ln in lines[1:]:
            if not ln.strip():
                break
            data.append(ln)
        last = data[-1].split('";"')[0].strip('"') if data else ""
        coms = sorted({ln.split('";"')[1].split(" - ")[0] for ln in data if '";"' in ln})
        present = {c: any(ln.startswith(f'"{c}"') for ln in data) for c in ORDER}
        trunc = len(data) == 100000
        after = [cm.UNSD_NAMES[c] for c in ORDER if c > last] if trunc else []
        rows.append(dict(file=Path(f).name, sha256=cm.sha256(Path(f)), data_rows=len(data), truncated_at_100000=trunc, last_country=last,
                         commodities=";".join(coms)[:300], asean_missing_after_cut=";".join(after),
                         asean_present=";".join(cm.UNSD_NAMES[c] for c in ORDER if present[c])))
        if trunc:
            ev.add(f"truncation.{Path(f).name}", dict(rows=len(data), last_country=last, asean_missing=after, commodities=coms), "mixed", "VERIFIED", "A",
                   f"pypsa-asean UNdata export {Path(f).name}")
    T = pd.DataFrame(rows)
    cm.write_csv(T.to_dict("records"), cm.TABLES / "W12_4_EXPORT_FILE_SCAN.csv")
    return T


def eb_gaps(ev: cm.Evidence) -> pd.DataFrame:
    x = pd.read_csv(cm.W11 / "ncv/UNSD_EXPORT_VS_EB2019_BY_FLOW.csv")
    gas = x[x.group == "natural_gas"]
    vint = {}
    for c in sorted(x.country.unique()):
        g = gas[(gas.country == c) & ~gas.flow.isin(["Exports", "Imports", "Primaryproduction"])]
        dev = float((g.ratio_pub_to_upstream - 0.9).abs().max()) if len(g) else None
        vint[c] = dict(gas_flows=int(len(g)), gas_max_dev=dev, layout=x[x.country == c].layout.iloc[0])
    for c, v in vint.items():
        v["vintage_consistent"] = bool(v["gas_max_dev"] is not None and v["gas_max_dev"] <= 0.005 and v["layout"] == "detailed")
        if v["gas_flows"] == 0:   # no domestic gas use: judge on oil road + households
            o = x[(x.country == c) & (x.group == "oil_products") & x.flow.isin(["Road", "Households", "Domesticaviation"])]
            v["oil_max_dev"] = float((o.ratio_pub_to_upstream - 1).abs().max()) if len(o) else None
            v["vintage_consistent"] = bool(v["layout"] == "detailed" and v["oil_max_dev"] is not None and v["oil_max_dev"] <= 0.01)
    rows = []
    for r in x.itertuples():
        exp_tj = r.tj_upstream_factors * (0.9 if r.group == "natural_gas" else 1.0)
        pub = r.tj_publication
        if r.flow in ("Exports", "Imports", "Primaryproduction"):
            continue
        pub_abs = abs(pub)
        gap = pub_abs - abs(exp_tj)
        cls = ("ncv (coal, W11)" if r.group.startswith("coal") else "vintage differs" if not vint[r.country]["vintage_consistent"]
               else "coverage (commodity absent)" if gap > 0.01 * max(pub_abs, 1.0) else "covered" if abs(gap) <= 0.01 * max(pub_abs, 1.0) else "export above publication")
        rows.append(dict(country=r.country, flow=r.flow, group=r.group, layout=r.layout, publication_tj=pub_abs, export_x_factors_tj=abs(exp_tj), gap_tj=gap,
                         gap_twh=gap / 3600.0, ratio=(pub_abs / abs(exp_tj)) if exp_tj else None, vintage_consistent=vint[r.country]["vintage_consistent"],
                         classification=cls, export_commodities=r.commodities))
    G = pd.DataFrame(rows)
    cm.write_csv(G.to_dict("records"), cm.TABLES / "W12_4_EB2019_GAP_BY_FLOW_GROUP.csv")
    cm.write_csv([dict(country=c, **v) for c, v in vint.items()], cm.TABLES / "W12_4_VINTAGE_FLAGS.csv")
    for c, v in vint.items():
        ev.add(f"eb.{c}.vintage_consistent", v["vintage_consistent"], "bool", "EXACT", "A", "W11 UNSD_EXPORT_VS_EB2019_BY_FLOW.csv",
               "natural gas publication / export TJ = 0.900 on every consumption flow (|dev| <= 0.005), detailed layout")
    for r in G[G.classification.str.startswith("coverage") & (G.gap_twh.abs() > 0.5)].itertuples():
        ev.add(f"eb.{r.country}.{r.flow}.{r.group}.gap_twh", r.gap_twh, "TWh (2019)", "EXACT", "A", "UN Energy Balances 2019 (W11) - export x upstream factors",
               f"ratio {r.ratio:.3f}")
    return G, vint


def parse_sdmx(codes: dict) -> pd.DataFrame:
    rows = []
    for cc in cm.ASEAN:
        p = SDMX / f"{cc}_2019_all.xml"
        root = ET.parse(p).getroot()
        for s in root.iter(f"{{{NS['g']}}}Series"):
            key = {v.get("id"): v.get("value") for v in s.find("g:SeriesKey", NS)}
            sa = s.find("g:Attributes", NS)
            satt = {v.get("id"): v.get("value") for v in (sa if sa is not None else [])}
            for o in s.findall("g:Obs", NS):
                if o.find("g:ObsDimension", NS).get("value") != "2019":
                    continue
                oa = o.find("g:Attributes", NS)
                oatt = {a.get("id"): a.get("value") for a in (oa if oa is not None else [])}
                v = float(o.find("g:ObsValue", NS).get("value"))
                unit = satt.get("UNIT_MEASURE", oatt.get("UNIT_MEASURE", ""))
                mult = int(oatt.get("UNIT_MULT", satt.get("UNIT_MULT", "0")) or 0)
                cf = float(oatt["CONVERSION_FACTOR"]) if "CONVERSION_FACTOR" in oatt else None
                q = v * 10 ** mult
                # TN / M3 with UNIT_MULT 3 = thousand t / thousand m3; CONVERSION_FACTOR in GJ per t or m3 -> TJ = q x CF / 1000;
                # TJ as reported (natural gas GCV in UNSD); GWh x 3.6 = TJ
                tj = (q * cf / 1e3) if (unit in ("TN", "M3") and cf is not None) else (q if unit == "TJ" else (q * 3.6 if unit == "GWHR" else None))
                rows.append(dict(cc=cc, commodity_code=key["COMMODITY"], commodity=codes["CL_COMMODITY_NRG"].get(key["COMMODITY"], ""),
                                 transaction_code=key["TRANSACTION"], transaction=codes["CL_TRANSACTION_NRG"].get(key["TRANSACTION"], ""), value=v, unit=unit,
                                 unit_mult=mult, conversion_factor=cf, tj=tj, obs_status=oatt.get("OBS_STATUS", "")))
    return pd.DataFrame(rows)


def sdmx_vs_export(S: pd.DataFrame, fuels: dict, ev: cm.Evidence):
    u = cm.load_unsd_2019()
    u = u[u.transaction.notna()].copy()
    u["c_n"] = u.commodity.map(norm); u["t_n"] = u.transaction.map(norm)
    S = S[~S.commodity.str.lower().str.startswith("of which")].copy()
    S["c_n"] = S.commodity.map(norm); S["t_n"] = S.transaction.map(norm)
    u["acc"] = u.t_n.map(lambda t: SECTOR_TX.get(t, (None, None))[1]); S["acc"] = S.t_n.map(lambda t: SECTOR_TX.get(t, (None, None))[1])
    exp_pairs = set(zip(u.ISO, u.c_n, u.acc)); exp_coms = set(zip(u.ISO, u.c_n))
    S["export_has_commodity"] = [(c, k) in exp_coms for c, k in zip(S.cc, S.c_n)]
    S["export_has_pair"] = [(c, k, a) in exp_pairs if a is not None else (c, k, t) in set(zip(u.ISO, u.c_n, u.t_n)) for c, k, a, t in zip(S.cc, S.c_n, S.acc, S.t_n)]
    dict_group = {norm(n): g for g, names in fuels.items() for n in names}
    extra = {"other vegetal material and residues": "biomass", "municipal wastes": "biomass", "industrial waste": "biomass", "animal waste": "biomass",
             "biogases": "biomass", "other liquid biofuels": "biomass", "other kerosene": "oil", "other oil products": "oil", "other oil products n.e.c.": "oil",
             "white spirit and special boiling point industrial spirits": "oil", "fuel oil": "oil", "aviation gasoline": "oil", "natural gas liquids": "oil",
             "blast furnace gas": "coal", "other recovered gases": "coal", "electricity": "electricity", "heat": "heat"}
    S["fuel_group"] = [dict_group.get(c, extra.get(c, "other")) for c in S.c_n]
    S["in_upstream_dictionary"] = [c in dict_group for c in S.c_n]
    m = S.t_n.map(lambda t: SECTOR_TX.get(t, (None, None)))
    S["model_sector"] = [x[0] for x in m]; S["d1_account"] = [x[1] for x in m]
    cm.write_csv(S.drop(columns=["c_n", "t_n"]).to_dict("records"), cm.TABLES / "W12_4_SDMX_2019_ALL.csv")
    miss = S[~S.export_has_pair & S.model_sector.notna() & (S.tj.fillna(0) > 0)].copy()
    miss["cause"] = np.where(~miss.export_has_commodity, "commodity absent from the export", "commodity present, this flow absent from the export")
    cm.write_csv(miss.drop(columns=["c_n", "t_n"]).to_dict("records"), cm.TABLES / "W12_4_SDMX_PAIRS_MISSING_IN_EXPORT.csv")
    # matched pairs: same-vintage check value by value (alias transactions of one account carry equal values -> max)
    um = u[u.acc.notna()].groupby(["ISO", "c_n", "acc", "t_n"]).q.sum().groupby(level=[0, 1, 2]).max()
    mt = S[S.export_has_pair & S.acc.notna()].copy()
    mt["export_value"] = [float(um.get((c, k, a), np.nan)) for c, k, a in zip(mt.cc, mt.c_n, mt.acc)]
    mt["ratio_sdmx_to_export"] = mt.value / mt.export_value.replace(0, np.nan)
    V = mt.groupby("cc").apply(lambda d: pd.Series(dict(pairs=len(d), equal_within_0p1pct=int(((d.ratio_sdmx_to_export - 1).abs() <= 1e-3).sum()),
                                                         share_equal=float(((d.ratio_sdmx_to_export - 1).abs() <= 1e-3).mean())))).reset_index()
    cm.write_csv(V.to_dict("records"), cm.TABLES / "W12_4_SDMX_EXPORT_VINTAGE.csv")
    # three-source decomposition per country x D1 account x fuel group: export (UNdata 2025-05, x SDMX conversion factor of the same pair),
    # SDMX 2019 of the same commodities (revision), SDMX commodities / flows the export lacks (coverage), UN Energy Balances 2019 publication
    mt["export_tj"] = mt.export_value * mt.tj / mt.value.replace(0, np.nan)
    eb = pd.read_csv(cm.W11 / "ncv/UNSD_EXPORT_VS_EB2019_BY_FLOW.csv")
    flow_acc = {"Households": "ResidentialFuel", "Commerce,publicservices": "ServicesFuel", "Agriculture,forestry,fishing": "AgricultureFinalEnergy",
                "Manufacturing,const.,mining": "IndustryFinalEnergy", "Road": "RoadResidualFuel", "Rail": "RailNonElectric", "Domesticaviation": "DomesticAviationFuel",
                "Domesticnavigation": "DomesticShippingFuel", "Otherconsumers": "OtherNEC", "Non-energyuse": "NonEnergy"}
    grp = {"biofuels": "biomass", "oil_products": "oil", "natural_gas": "gas", "coal_primary": "coal", "coal_products": "coal"}
    eb = eb[eb.flow.isin(flow_acc) & eb.group.isin(grp)].assign(acc=lambda d: d.flow.map(flow_acc), fg=lambda d: d.group.map(grp))
    eb_tj = eb.groupby(["country", "acc", "fg"]).tj_publication.sum().abs()
    eb_exp = eb.assign(x=np.where(eb.group == "natural_gas", eb.tj_upstream_factors * 0.9, eb.tj_upstream_factors)).groupby(["country", "acc", "fg"]).x.sum().abs()
    keys = set(zip(mt.cc, mt.acc, mt.fuel_group)) | set(zip(miss.cc, miss.d1_account, miss.fuel_group)) | set(eb_tj.index)
    tri = []
    for c, a, f in sorted(k for k in keys if k[1] is not None and k[2] in ("biomass", "oil", "gas", "coal", "electricity")):
        m1 = mt[(mt.cc == c) & (mt.acc == a) & (mt.fuel_group == f)]
        m2 = miss[(miss.cc == c) & (miss.d1_account == a) & (miss.fuel_group == f)]
        tri.append(dict(country=c, d1_account=a, fuel_group=f, export_tj=float(m1.export_tj.sum()), sdmx_same_commodities_tj=float(m1.tj.sum()),
                        revision_tj=float(m1.tj.sum() - m1.export_tj.sum()), sdmx_missing_in_export_tj=float(m2.tj.sum()),
                        missing_commodities=";".join(sorted(set(m2.commodity))), eb2019_publication_tj=float(eb_tj.get((c, a, f), np.nan)),
                        eb2019_export_x_factors_tj=float(eb_exp.get((c, a, f), np.nan)),
                        eb_minus_export_tj=float(eb_tj.get((c, a, f), np.nan) - eb_exp.get((c, a, f), np.nan))))
    TRI = pd.DataFrame(tri)
    for k in ("export_tj", "sdmx_same_commodities_tj", "revision_tj", "sdmx_missing_in_export_tj", "eb2019_publication_tj", "eb_minus_export_tj"):
        TRI[k.replace("_tj", "_twh")] = TRI[k] / 3600.0
    cm.write_csv(TRI.to_dict("records"), cm.TABLES / "W12_4_THREE_SOURCE_BY_ACCOUNT.csv")
    for r in TRI[(TRI.sdmx_missing_in_export_twh > 0.5) | (TRI.revision_twh.abs() > 2) | (TRI.eb_minus_export_twh.abs() > 2)].itertuples():
        ev.add(f"tri.{r.country}.{r.d1_account}.{r.fuel_group}", dict(export_twh=r.export_twh, revision_twh=r.revision_twh, missing_twh=r.sdmx_missing_in_export_twh,
                                                                      eb_minus_export_twh=r.eb_minus_export_twh), "TWh (2019)", "EXACT", "A",
               "W12_4_THREE_SOURCE_BY_ACCOUNT.csv (UNdata export / SDMX 2019 / UN Energy Balances 2019)")
    agg = miss.groupby(["cc", "model_sector", "d1_account", "fuel_group", "commodity", "cause", "in_upstream_dictionary"]).tj.sum().reset_index()
    agg["twh"] = agg.tj / 3600.0
    cm.write_csv(agg.to_dict("records"), cm.TABLES / "W12_4_MISSING_BY_COUNTRY_SECTOR_COMMODITY.csv")
    for r in agg[agg.twh > 0.5].itertuples():
        ev.add(f"sdmx.{r.cc}.{r.d1_account}.{r.commodity}.twh", r.twh, "TWh (2019)", "VERIFIED", "A", f"sdmx/{r.cc}_2019_all.xml (UNSD SDMX, CONVERSION_FACTOR)",
               f"{r.cause}; upstream dictionary has it: {r.in_upstream_dictionary}")
    for r in V.itertuples():
        ev.add(f"sdmx.{r.cc}.share_pairs_equal_to_export", r.share_equal, "ratio", "EXACT", "A", "W12_4_SDMX_EXPORT_VINTAGE.csv", f"{r.pairs} matched pairs")
    return S, miss, agg, V


def model_scale(agg: pd.DataFrame, ev: cm.Evidence) -> pd.DataFrame:
    ats = pd.read_csv(cm.REPO / "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False, dtype=str)
    ats["b"] = pd.to_numeric(ats.base_2019_mwh, errors="coerce").fillna(0.0); ats["v"] = pd.to_numeric(ats.value_2050_mwh, errors="coerce").fillna(0.0)
    car = {"biomass": "biomass", "oil": "oil", "gas": "gas", "coal": "coal", "electricity": "electricity"}
    out = []
    g = agg[agg.fuel_group.isin(list(car))].groupby(["cc", "model_sector", "d1_account", "fuel_group"]).agg(twh=("twh", "sum"), commodities=("commodity", lambda s: ";".join(sorted(set(s))))).reset_index()
    for r in g.itertuples():
        a = ats[(ats.country == r.cc) & (ats.account == r.d1_account) & (ats.carrier == car[r.fuel_group])]
        if r.d1_account == "IndustryFinalEnergy" and not len(a):
            a = ats[(ats.country == r.cc) & (ats.sector == "Industry")]
        sec = ats[(ats.country == r.cc) & (ats.sector == r.model_sector)]
        mult = float(pd.to_numeric(a.multiplier_total, errors="coerce").dropna().iloc[0]) if len(a) and pd.to_numeric(a.multiplier_total, errors="coerce").notna().any() else (
            float(pd.to_numeric(sec.multiplier_total, errors="coerce").dropna().iloc[0]) if len(sec) and pd.to_numeric(sec.multiplier_total, errors="coerce").notna().any() else None)
        base_row = float(a.b.sum()) if len(a) else 0.0
        sec_base = float(sec[sec.carrier != "electricity"].b.sum()) if len(sec) else 0.0
        out.append(dict(country=r.cc, model_sector=r.model_sector, d1_account=r.d1_account, fuel_group=r.fuel_group, commodities=r.commodities, missing_2019_twh=r.twh,
                        d1_row_present=bool(len(a)), d1_row_base_2019_twh=base_row / 1e6, sector_fuel_base_2019_twh=sec_base / 1e6,
                        missing_share_of_sector_fuel=(r.twh * 1e6 / sec_base) if sec_base else None, ats_multiplier=mult,
                        reading_I_2050_twh=(r.twh * mult) if mult is not None else None))
    M = pd.DataFrame(out)
    cm.write_csv(M.to_dict("records"), cm.TABLES / "W12_4_MODEL_SCALE_READING_I.csv")
    for r in M[M.missing_2019_twh > 0.5].itertuples():
        ev.add(f"model.{r.country}.{r.d1_account}.{r.fuel_group}.reading_I_2050_twh", r.reading_I_2050_twh, "TWh (2050)", "INFERENCE", "C", "W12_4_MODEL_SCALE_READING_I.csv",
               f"missing 2019 {r.missing_2019_twh:.3f} TWh x ATS multiplier {r.ats_multiplier}")
    return M


def main():
    ev = cm.Evidence("W12_4")
    T = truncation_scan(ev)
    G, vint = eb_gaps(ev)
    codes = json.loads((cm.REPO / "research_inputs/assembly_v1/sources/unsd_targeted/codelists.json").read_text())
    fz = json.loads((cm.REPO / "research_inputs/assembly_v1/sources/FROZEN_UPSTREAM_CONVERSIONS.json").read_text())["constants"]
    fuels = {"oil": fz["oil_fuels"], "gas": fz["gas_fuels"], "coal": fz["coal_fuels"], "biomass": fz["biomass_fuels"], "electricity": fz["electricity"], "heat": fz["heat"]}
    S = parse_sdmx(codes)
    rec = []
    for f in sorted(SDMX.glob("*_2019_all.xml.receipt.json")):
        r = json.loads(f.read_text()); rec.append(dict(path=f"sdmx/{r['file']}", bytes=r["bytes"], sha256=r["sha256"], url=r["url"], final_url=r["final_url"], retrieved_utc=r["utc"],
                                                    http_status=r["http_status"], source="UNSD SDMX web service (dataflow UNSD,DF_UNDATA_ENERGY v1.2), same public interface as research_inputs/assembly_v1/sources/unsd_targeted/; no login",
                                                    licence="UN data terms of use (as for the repository unsd_targeted files; not re-checked online)", used_by="scripts/w12_coverage.py"))
        ev.add(f"sdmx_file.{r['file']}", r["sha256"], "sha256", "VERIFIED", "A", r["url"], f"retrieved {r['utc']}, {r['bytes']} bytes")
    cm.write_csv(rec, cm.W12 / "DATA_REGISTRY_W12_SDMX.csv")
    S, miss, agg, V = sdmx_vs_export(S, fuels, ev)
    M = model_scale(agg, ev)
    p = ev.write()
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 70); pd.set_option("display.max_rows", 300)
    print(T[["file", "data_rows", "truncated_at_100000", "last_country", "asean_missing_after_cut", "commodities"]].sort_values("data_rows").tail(6).to_string())
    print(pd.DataFrame(vint).T.to_string())
    print(G[G.classification.str.startswith("coverage") & (G.gap_twh > 0.3)][["country", "flow", "group", "publication_tj", "export_x_factors_tj", "gap_twh", "ratio"]].to_string())
    print(V.to_string())
    print(agg[agg.twh > 0.3].sort_values(["cc", "twh"], ascending=[True, False]).to_string())
    print(M[M.missing_2019_twh > 0.3].to_string())
    TRI = pd.read_csv(cm.TABLES / "W12_4_THREE_SOURCE_BY_ACCOUNT.csv")
    print(TRI[(TRI.sdmx_missing_in_export_twh > 0.5) | (TRI.revision_twh.abs() > 2) | (TRI.eb_minus_export_twh.abs() > 2)][
        ["country", "d1_account", "fuel_group", "export_twh", "revision_twh", "sdmx_missing_in_export_twh", "eb2019_publication_twh", "eb_minus_export_twh"]].round(2).to_string())
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
