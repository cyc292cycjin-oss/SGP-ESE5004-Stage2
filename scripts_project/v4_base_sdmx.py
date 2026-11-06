"""V4 W08 checklist section 1 (decision 210 item 1): the 2019 base year from the UNSD SDMX current database.

    PYTHONHASHSEED=0 python scripts_project/v4_base_sdmx.py            # writes the capsule, the blend memo and the v4 D1 base table
    PYTHONHASHSEED=0 python scripts_project/v4_base_sdmx.py --gates    # reproduction gates G1-G3 on the old capsule only

Code moved from the I1 / I2 scratch scripts without changing the rules (work/p1_v4_w07_20261106/I1/scripts/i1_sdmx.py, i1_base.py):
  capsule()       the eleven SDMX responses (research_inputs/assembly_v1/sources/unsd_sdmx_2019/, W12 retrieval 2026-11-05) -> capsule-format records
                  (export naming, export units, Decimal rescaling), blend memo rows ('Of which' biofuel quantities), left-out items;
  Recon           factor modes on top of reconstruct_base_accounts.Reconstruction (I1 Recon; the repository module itself stays the frozen v3.1
                  path and is not edited): 'd207' = SDMX CONVERSION_FACTOR for every mass / volume row with the
                  exceptions of research_inputs/demand_v5/NCV_EXCEPTIONS.csv (ID hard coal 20.29, ID coke oven coke 28.20);
  blend()         generalised blend rule ('Of which' memo where UNSD publishes one, else maximum overlap) - I1 i1_base.blend;
  rail_children() rail parent kept as accounting, carrier children added (reconstruct_base_accounts.py lines 225-234) - I1 i1_base.rail_children;
  d1_rows()       D1 base rows as d1_demand_2050.py main() lines 166-200 (accounts, electricity by sector, non-energy rows, marine-bunker EB override).
Gates (I1): G1 reconstruct(sources) = BASE_RECONSTRUCTION.json; G2 D1 rows = base_2019_mwh of the D1 table (string-exact after d1_common.fmt);
G3 the generalised blend rule on the unchanged capsule = the G2 rows.
Outputs: research_inputs/assembly_v1/sources/SDMX_2019_CAPSULE.json, SDMX_2019_BLEND_MEMO.csv; research_inputs/industry_v4/D1_BASE2019_SDMX.csv
(country, sector, carrier, account, base_2019_mwh, base_status: the v4 seed 'S5p'), HOUSEHOLD_GASOLINE_2019.csv (ResidentialFuel motor gasoline of
the same base, decision 210 item 6), BASE2019_SDMX_EVIDENCE.json. Nothing is solved; the v3.1 D1 table is not touched.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path

import pandas as pd

import reconstruct_base_accounts as rba
from d1_common import SRC_DIR, fmt
from d1_demand_2050 import ACCOUNT_SECTOR, BUNKER_EB_CSV, NONENERGY_CARRIER, SECTORS, electricity_by_sector
from v4_common import DEMAND_DIR, SDMX_DIR, SRC, V4_DIR, sha256

ASEAN = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]   # I1 order (row order of the written base only)
UNSD_NAMES = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID", "Lao People's Dem. Rep.": "LA", "Malaysia": "MY", "Myanmar": "MM",
              "Philippines": "PH", "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "Viet Nam": "VN"}
CC_NAME = {v: k for k, v in UNSD_NAMES.items()}
NS = {"g": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic", "m": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"}
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
BIO_PEER = {"biodiesel": "gas oil/ diesel oil", "biogasoline": "motor gasoline", "bio jet kerosene": "kerosene-type jet fuel"}
MEMO_CODE = {"biodiesel": "5222", "biogasoline": "5212", "bio jet kerosene": "5232"}
NEU_EXTRA = {"Other oil products n.e.c.": "oil", "White spirit and special boiling point industrial spirits": "oil", "Other kerosene": "oil",
             "Kerosene-type Jet Fuel": "oil", "Refinery gas": "oil", "Conventional crude oil": "oil", "Additives and Oxygenates": "oil",
             "Coking coal": "coal", "Other bituminous coal": "coal", "Sub-bituminous coal": "coal", "Lignite": "coal", "Anthracite": "coal",
             "Coke oven coke": "coal", "Charcoal": "biomass", "Other Vegetal Material and Residues": "biomass", "Fuelwood": "biomass",
             "Biodiesel": "biomass", "Biogasoline": "biomass", "Aviation gasoline": "oil", "Liquified Petroleum Gas (LPG)": "oil",
             "Natural Gas (including LNG)": "gas", "Petroleum Coke": "oil", "Refinery Gas": "oil", "Coke-oven coke": "coal"}
ELEC_LABEL = {"12": "Electricity - Final energy consumption", "121": "Electricity - Consumption by manufacturing, construction and non-fuel industry",
              "1231": "Electricity - Consumption by households", "1235": "Electricity - Consumption by commercial and public services",
              "1232": "Electricity - Consumption in agriculture, forestry and fishing", "122": "Electricity - Consumption by transport",
              "1222": "Electricity - Consumption by rail", "1234": "Electricity - Consumption not elsewhere specified (other)", "123": "Electricity - Consumption by other"}
TX_CODE_ACCOUNT = {"1221": "RoadResidualFuel", "1222": "TransportEmbeddedFuelParent", "121": "IndustryFinalEnergy", "1235": "ServicesFuel",
                   "1232": "AgricultureFinalEnergy", "1231": "ResidentialFuel", "1223": "DomesticAviationFuel", "1224": "DomesticShippingFuel",
                   "1225": "TransportNEC", "1234": "OtherNEC"}
NEU_TX = {"non-energy uses", "consumption for non-energy uses"}
CAPSULE = SRC / "SDMX_2019_CAPSULE.json"
MEMO_CSV = SRC / "SDMX_2019_BLEND_MEMO.csv"
BASE_CSV = V4_DIR / "D1_BASE2019_SDMX.csv"
GASOLINE_CSV = V4_DIR / "HOUSEHOLD_GASOLINE_2019.csv"
EVIDENCE = V4_DIR / "BASE2019_SDMX_EVIDENCE.json"
SOURCE_LABEL = "UNSD SDMX DF_UNDATA_ENERGY v1.2, W12 retrieval 2026-11-05T19:44-19:45 UTC"


def write_csv_i1(rows: list[dict], path: Path, cols: list[str] | None = None) -> Path:
    """I1 i1_common.write_csv (floats %.9g, LF)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if cols is None:
        cols = []
        for r in rows:
            for k in r:
                if k not in cols:
                    cols.append(k)
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n", extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.9g}" if isinstance(r.get(k), float) else r.get(k))) for k in cols})
    return path


def write_json_i1(obj, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=False, default=float)
        f.write("\n")
    return path


# ======================================================================================================== SDMX responses -> capsule
def responses() -> pd.DataFrame:
    """Integrity of the eleven responses against the W12 registry rows (SHA256, bytes), the XML header Prepared time, years, footer / error."""
    reg = pd.read_csv(SDMX_DIR / "SDMX_RESPONSES_REGISTRY_W12.csv").set_index("path")
    rows = []
    for cc in ASEAN:
        p = SDMX_DIR / f"{cc}_2019_all.xml"
        root = ET.parse(p).getroot(); hdr = root.find("m:Header", NS)
        prepared = hdr.find("m:Prepared", NS).text if hdr is not None and hdr.find("m:Prepared", NS) is not None else ""
        footer = [e for e in root.iter() if e.tag.endswith("Footer") or e.tag.endswith("ErrorMessage")]
        years, nobs = set(), 0
        for s in root.iter(f"{{{NS['g']}}}Series"):
            for o in s.findall("g:Obs", NS):
                years.add(o.find("g:ObsDimension", NS).get("value")); nobs += 1
        r = reg.loc[f"sdmx/{p.name}"]
        rows.append(dict(country=cc, file=p.name, bytes=p.stat().st_size, sha256=sha256(p), sha256_w12=r.sha256, bytes_w12=int(r.bytes), url=r.url,
                         retrieved_utc=r.retrieved_utc, prepared=prepared, observations=nobs, years=";".join(sorted(years)), footer_or_error=len(footer)))
    T = pd.DataFrame(rows)
    T["ok"] = (T.sha256 == T.sha256_w12) & (T.bytes == T.bytes_w12) & (T.years == "2019") & (T.footer_or_error == 0)
    if not T.ok.all():
        raise SystemExit("STOP: an SDMX response differs from the W12 registry or fails the integrity check")
    return T


def parse(codes: dict) -> pd.DataFrame:
    rows = []
    for cc in ASEAN:
        p = SDMX_DIR / f"{cc}_2019_all.xml"
        root = ET.parse(p).getroot()
        for s in root.iter(f"{{{NS['g']}}}Series"):
            key = {v.get("id"): v.get("value") for v in s.find("g:SeriesKey", NS)}
            sa = s.find("g:Attributes", NS)
            satt = {v.get("id"): v.get("value") for v in (sa if sa is not None else [])}
            for o in s.findall("g:Obs", NS):
                oa = o.find("g:Attributes", NS)
                att = {**satt, **{a.get("id"): a.get("value") for a in (oa if oa is not None else [])}}
                rows.append(dict(country=cc, commodity_code=key["COMMODITY"], commodity_sdmx=codes["CL_COMMODITY_NRG"].get(key["COMMODITY"], ""),
                                 transaction_code=key["TRANSACTION"], transaction_sdmx=codes["CL_TRANSACTION_NRG"].get(key["TRANSACTION"], ""),
                                 value_raw=o.find("g:ObsValue", NS).get("value"), unit=att.get("UNIT_MEASURE", ""), unit_mult=att.get("UNIT_MULT", "0"),
                                 obs_status=att.get("OBS_STATUS", ""), conversion_factor=att.get("CONVERSION_FACTOR", ""), source_file=f"sdmx/{p.name}"))
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
                                transaction=r.transaction_sdmx, unit=r.unit))
            continue
        uname, scale = UNIT[r.unit]
        q = D(r.value_raw) * (D(10) ** (int(r.unit_mult) - scale))
        com = SDMX_TO_EXPORT[r.commodity_code]
        recs.append({"Country or Area": CC_NAME[r.country], "Commodity - Transaction": f"{com} - {r.transaction_sdmx}", "Year": "2019", "Unit": uname,
                     "Quantity": format(q.normalize(), "f") if q != 0 else "0", "Quantity Footnotes": r.obs_status, "Country": r.country, "Commodity": com,
                     "Transaction": r.transaction_sdmx, "SourceFile": r.source_file, "SourceSHA256": shas[r.country],
                     "PhysicalLine": f"{r.commodity_code}:{r.transaction_code}", "CommodityCode": r.commodity_code, "TransactionCode": r.transaction_code,
                     "CONVERSION_FACTOR": r.conversion_factor, "OBS_STATUS": r.obs_status})
    return recs, memo, dropped


# ======================================================================================================== base rebuild (I1 i1_base, unchanged rules)
def ext_conversion(conv: dict) -> dict:
    ext = json.loads((SRC / "SDMX_DICTIONARY_EXTENSION.json").read_text())
    c = copy.deepcopy(conv)
    for k in ("biomass_fuels", "oil_fuels", "coal_fuels"):
        c["constants"][k] = list(c["constants"][k]) + list(ext[k])
    return c


def ncv_exceptions() -> dict:
    t = pd.read_csv(DEMAND_DIR / "NCV_EXCEPTIONS.csv", dtype=str)
    return {(r.country, r.commodity): r.gj_per_unit for r in t.itertuples()}


def rail_children(result: dict) -> None:
    for a in list(result["accounts"]):
        if a["Account"] != "TransportEmbeddedFuelParent" or not a["SourceRows"]:
            continue
        for fuel, value in a["CarrierBreakdownMWh"].items():
            selected = [r for r in result["selected_rows"] if r["RowID"] in a["SourceRows"] and r["Carrier"] == fuel]
            child = dict(a, Account="RailNonElectric", Carrier=fuel, AccountID=a["Country"] + ":2019:RailNonElectric:" + fuel, ValueMWh=value,
                         CarrierBreakdownMWh={fuel: value}, SourceRows=[r["RowID"] for r in selected], ParentAccountID=a["AccountID"])
            result["accounts"].append(child)
        for r in result["selected_rows"]:
            if r["RowID"] in a["SourceRows"]:
                r["Account"] = "RailNonElectric"; r["OriginalParentAccount"] = "TransportEmbeddedFuelParent"


def blend(result: dict, memo: dict, log: list, label: str) -> None:
    rows = result["selected_rows"]
    by_acc = defaultdict(list)
    for r in rows:
        by_acc[(r["Country"], r.get("OriginalParentAccount", r["Account"]))].append(r)
    for (c, acc), rs in by_acc.items():
        for b in rs:
            bc = rba.commodity(b["Commodity"])
            if bc not in BIO_PEER or D(b["MWh"]) <= 0:
                continue
            peers = [p for p in rs if rba.commodity(p["Commodity"]) == BIO_PEER[bc]]
            if not peers:
                continue
            if len(peers) != 1 or peers[0]["RawUnit"] != b["RawUnit"]:
                raise ValueError(f"blend: ambiguous peer {c} {acc} {bc}")
            p = peers[0]
            P, B = D(p["RawValue"]), D(b["RawValue"])
            mk = (c, MEMO_CODE[bc], acc)
            Z, rule = (memo[mk], "memo (UNSD 'Of which' quantity)") if mk in memo else (B, "maximum overlap (whole biofuel blended)")
            Z = min(Z, P)
            f = D(p["MWh"]) / P if P else D(0)
            cut = Z * f
            p["MWh"] = str(D(p["MWh"]) - cut); p.setdefault("BlendCutMWh", "0"); p["BlendCutMWh"] = str(D(p["BlendCutMWh"]) + cut)
            for a in result["accounts"]:
                if a["Country"] == c and p["RowID"] in a["SourceRows"] and a["Carrier"] == "oil":
                    a["ValueMWh"] = str(D(a["ValueMWh"]) - cut)
                    a["CarrierBreakdownMWh"]["oil"] = str(D(a["CarrierBreakdownMWh"]["oil"]) - cut)
                    a["BlendRule"] = rule
                if a["Country"] == c and (p["RowID"] in a["SourceRows"] or b["RowID"] in a["SourceRows"]) and a["Status"] == "UNRESOLVED_BIOFUEL_OVERLAP":
                    a["Status"] = "NUMERIC_INPUT_READY"; a["Classification"] = "REQUIRED_PHYSICAL"; a["Reason"] = "blend resolved: " + rule
            log.append(dict(step=label, country=c, account=acc, bio=b["Commodity"], petroleum=p["Commodity"], P_kt=str(P), B_kt=str(B), Z_kt=str(Z),
                            rule=rule, petroleum_mwh_cut=str(cut)))


def d1_rows(result: dict, elec_records: list, blend_baseline: dict | None, eb: dict) -> pd.DataFrame:
    rows = []
    for a in result["accounts"]:
        c, acc, car = a["Country"], a["Account"], a["Carrier"]
        st = a["Status"]
        if blend_baseline is not None and a["AccountID"] in blend_baseline:
            val, bst = float(blend_baseline[a["AccountID"]]["BaseMWh"]), "ACCEPTED_BLEND_BASELINE_A"
        elif st == "NUMERIC_INPUT_READY":
            val, bst = float(a["ValueMWh"]), st
        elif st in ("SOURCE_BOUNDED_ZERO", "BOUNDARY_EXCLUSION"):
            val, bst = 0.0, st
        else:
            val, bst = (float(a["ValueMWh"]) if a.get("ValueMWh") not in (None, "") else 0.0), st
        rows.append(dict(country=c, sector=ACCOUNT_SECTOR[acc], carrier=car, account=acc, base_2019_mwh=val, base_status=bst))
    es = electricity_by_sector(elec_records)
    for c in ASEAN:
        for s in SECTORS:
            rows.append(dict(country=c, sector=s, carrier="electricity", account="UNSD_electricity_" + s, base_2019_mwh=es[c][s], base_status="NUMERIC_INPUT_READY"))
    for ne in result["nonenergy_reference"]:
        car = NONENERGY_CARRIER.get(ne["Commodity"], NEU_EXTRA.get(ne["Commodity"]))
        if car is None:
            raise KeyError("non-energy carrier unknown: " + ne["Commodity"])
        rows.append(dict(country=ne["Country"], sector="NonEnergyUse", carrier=car, account="NonEnergy:" + ne["Commodity"], base_2019_mwh=float(ne["MWh"]),
                         base_status="NONENERGY_REFERENCE"))
    df = pd.DataFrame(rows)
    for i in df.index[(df.sector == "InternationalBunkers") & (df.account == "InternationalShippingBunker") & df.country.isin(sorted({k[0] for k in eb}))]:
        df.at[i, "base_2019_mwh"] = float(eb[(df.at[i, "country"], "International marine bunkers")]["value_MWh"]); df.at[i, "base_status"] = "UNSD_EB_2019_NO_FLOW_ZERO"
    return df


class Recon(rba.Reconstruction):
    """I1 i1_base.Recon (moved unchanged; reconstruct_base_accounts.py itself stays the frozen v3.1 path): factor mode 'frozen' (frozen factors,
    SDMX CONVERSION_FACTOR only for commodities without a frozen factor), 'sdmx' (SDMX CONVERSION_FACTOR for every mass / volume row), 'd207'
    ('sdmx' with the per-country exceptions of NCV_EXCEPTIONS.csv: ID hard coal 20.29, ID coke oven coke 28.20; decisions 207 / 210)."""

    def __init__(self, source, conversion, mode="frozen", exceptions=None):
        self.mode = mode
        self.exceptions = {(k[0], rba.commodity(k[1])): str(v) for k, v in (exceptions or {}).items()}
        super().__init__(source, conversion)

    def convert(self, r):
        c = rba.commodity(r["Commodity"]); unit = r["Unit"]; f = self.fuels.get(c)
        cf = r.get("CONVERSION_FACTOR") or ""
        if unit in ("Metric tons,  thousand", "Cubic metres, thousand") and f not in (None, "electricity"):
            new_com = c not in self.factors
            if self.mode in ("sdmx", "d207") or new_com:
                exc = self.mode == "d207" and (r["Country"], c) in self.exceptions
                if exc:
                    cf = self.exceptions[(r["Country"], c)]
                if cf:
                    q = rba.decimal(r["Quantity"])
                    return q * D(cf) * 1000 / D("3.6"), f"{unit} x SDMX CONVERSION_FACTOR {cf} GJ/unit x 1000 / 3.6", \
                        ("NCV_DECISION_207" if exc else "NCV_SDMX_CONVERSION_FACTOR")
                if new_com:
                    raise ValueError("No frozen factor and no SDMX factor: " + c)
        return super().convert(r)


class ZeroScope(Recon):
    """Zero proofs bounded to one source version; a proof that meets mixed versions is recorded instead of raising (I1)."""
    errors_log: list = []

    def reported_zero_bound(self, c, account, fuel):
        try:
            return super().reported_zero_bound(c, account, fuel)
        except ValueError as exc:
            ZeroScope.errors_log.append(dict(country=c, account=account, fuel=fuel, error=str(exc)))
            return None


def build_version(records: list, conv: dict, mode: str, memo: dict, log: list, label: str, zero_records: list | None = None, dropped_neu: list | None = None) -> dict:
    exc = ncv_exceptions()
    fuels = Recon(dict(records=[]), conv, mode, exc).fuels
    keep = []
    for r in records:
        if rba.norm(r["Transaction"]) in NEU_TX and r["Commodity"] and fuels.get(rba.commodity(r["Commodity"])) is None:
            if dropped_neu is not None:
                dropped_neu.append(dict(step=label, country=r["Country"], commodity=r["Commodity"], quantity=r["Quantity"], unit=r["Unit"]))
            continue
        keep.append(r)
    rec = Recon(dict(records=keep), conv, mode, exc)
    rec.zero_scope = ZeroScope(dict(records=copy.deepcopy(zero_records if zero_records is not None else keep)), conv, mode, exc)
    res = rec.build()
    rail_children(res)
    blend(res, memo, log, label)
    return res


def memo_dict(memo_rows: pd.DataFrame) -> dict:
    return {(r.country, r.memo_code, TX_CODE_ACCOUNT[r.transaction_code]): D(r.value_raw) for r in memo_rows.itertuples() if r.transaction_code in TX_CODE_ACCOUNT}


def elec_records_sdmx(cap: list) -> list:
    return [{"Country or Area": CC_NAME[r["Country"]], "Commodity - Transaction": ELEC_LABEL[r["TransactionCode"]], "Year": "2019",
             "Unit": r["Unit"], "Quantity": r["Quantity"], "Quantity Footnotes": r["OBS_STATUS"], "Country": r["Country"]}
            for r in cap if r["CommodityCode"] == "7000" and r["TransactionCode"] in ELEC_LABEL]


def gates(memo: dict | None = None) -> dict:
    """I1 G1-G3 on the old capsule: the repository path and the generalised blend rule reproduce the v3.1 base."""
    conv = json.loads((SRC / "FROZEN_UPSTREAM_CONVERSIONS.json").read_text())
    blend_bl = {v["BaseAccountID"]: v for v in json.loads((SRC / "ASSEMBLY_V1_BLEND_BASELINE.json").read_text())["records"].values()}
    elec_exp = json.loads((SRC / "electricity.json").read_text())["records"]
    eb = {(r["iso2"], r["flow"]): r for r in pd.read_csv(SRC_DIR / BUNKER_EB_CSV, dtype=str).to_dict("records")}
    repo_base = json.loads((SRC / "BASE_RECONSTRUCTION.json").read_text())
    key = ["country", "sector", "carrier", "account"]
    r0 = rba.reconstruct(SRC)
    acc_repo = {a["AccountID"]: (a["ValueMWh"], a["Status"]) for a in repo_base["accounts"]}
    acc_new = {a["AccountID"]: (a["ValueMWh"], a["Status"]) for a in r0["accounts"]}
    D0 = d1_rows(r0, elec_exp, blend_bl, eb)
    d1s = pd.read_csv(DEMAND_DIR / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", keep_default_na=False, dtype=str)
    m = d1s[key + ["base_2019_mwh"]].merge(D0[key + ["base_2019_mwh"]], on=key, how="outer", suffixes=("_repo", "_new"), indicator=True)
    m["new_fmt"] = [fmt(v) if pd.notna(v) else "" for v in m.base_2019_mwh_new]
    if memo is None:
        memo = memo_dict(pd.read_csv(MEMO_CSV, dtype=str))
    cap0 = json.loads((SRC / "UNSD_2019_SOURCE_CAPSULE.json").read_text())["records"]
    cap_frozen = copy.deepcopy(cap0)
    ov = json.loads((SRC / "TH_ROAD_LOCAL_VINTAGE_APPLIED.json").read_text())
    byid = {rba.row_id(r): i for i, r in enumerate(cap0)}
    for e in ov["replacements"]:
        cap0[byid[e["OldRowID"]]] = e["NewRawRow"]
    S0 = build_version(copy.deepcopy(cap0), conv, "frozen", memo, [], "S0", cap_frozen)
    D0g = d1_rows(S0, elec_exp, None, eb)
    m3 = D0[key + ["base_2019_mwh"]].merge(D0g[key + ["base_2019_mwh"]], on=key, how="outer", suffixes=("_repo", "_gen"), indicator=True)
    dmax = float((m3.base_2019_mwh_repo - m3.base_2019_mwh_gen).abs().max())
    return dict(G1=bool(acc_repo == acc_new), G1_accounts=len(acc_new), G2=bool((m._merge == "both").all() and (m.base_2019_mwh_repo == m.new_fmt).all()),
                G2_rows=int(len(m)), G2_unmatched=int((m._merge != "both").sum()), G3=bool((m3._merge == "both").all() and dmax <= 1e-6), G3_max_abs_mwh=dmax)


def compute() -> dict:
    """Everything in memory (no file written): responses, capsule, memo, the S5p rebuild, the D1 base rows and the household gasoline."""
    T = responses()
    codes = json.loads((SRC / "unsd_targeted/codelists.json").read_text())
    O = parse(codes)
    shas = dict(zip(T.country, T.sha256))
    recs, memo_rows, dropped = capsule(O, shas)
    conv = json.loads((SRC / "FROZEN_UPSTREAM_CONVERSIONS.json").read_text())
    memo = memo_dict(pd.DataFrame(memo_rows).astype(str))
    eb = {(r["iso2"], r["flow"]): r for r in pd.read_csv(SRC_DIR / BUNKER_EB_CSV, dtype=str).to_dict("records")}
    log, dropped_neu = [], []
    ZeroScope.errors_log = []
    S5p = build_version(copy.deepcopy(recs), ext_conversion(conv), "d207", memo, log, "S5p", dropped_neu=dropped_neu)
    DR = d1_rows(S5p, elec_records_sdmx(recs), None, eb)
    gas = {}
    for r in S5p["selected_rows"]:
        if r["Account"] == "ResidentialFuel" and rba.commodity(r["Commodity"]) == "motor gasoline":
            gas[r["Country"]] = gas.get(r["Country"], 0.0) + float(r["MWh"])
    return dict(T=T, shas=shas, recs=recs, memo_rows=memo_rows, dropped=dropped, log=log, dropped_neu=dropped_neu, S5p=S5p, DR=DR, gas=gas)


def capsule_obj(x: dict) -> dict:
    return dict(schema="i1-sdmx-capsule-1", year=2019, source=SOURCE_LABEL, files={f"sdmx/{cc}_2019_all.xml": x["shas"][cc] for cc in ASEAN}, records=x["recs"])


def build_sdmx_base() -> dict:
    x = compute()
    T, recs, memo_rows, dropped, log, dropped_neu, DR, gas = x["T"], x["recs"], x["memo_rows"], x["dropped"], x["log"], x["dropped_neu"], x["DR"], x["gas"]
    write_json_i1(capsule_obj(x), CAPSULE)
    write_csv_i1(memo_rows, MEMO_CSV)
    V4_DIR.mkdir(parents=True, exist_ok=True)
    DR.to_csv(BASE_CSV, index=False, lineterminator="\n")
    pd.DataFrame([dict(country=c, account="ResidentialFuel", commodity="motor gasoline", base_2019_mwh=gas.get(c, 0.0),
                       source="UNSD SDMX 2019 households (1231) motor gasoline, v4 base (D1_BASE2019_SDMX.csv rule)") for c in ASEAN]).to_csv(GASOLINE_CSV, index=False, lineterminator="\n")
    ev = dict(script="scripts_project/v4_base_sdmx.py", responses=T.drop(columns=["ok"]).to_dict("records"), capsule=dict(file=CAPSULE.name, sha256=sha256(CAPSULE), records=len(recs)),
              blend_memo=dict(file=MEMO_CSV.name, sha256=sha256(MEMO_CSV), rows=len(memo_rows)), left_out=len(dropped), neu_rows_without_fuel_group=dropped_neu,
              zero_proof_not_possible=ZeroScope.errors_log, blend_log=log, base=dict(file=BASE_CSV.name, sha256=sha256(BASE_CSV), rows=len(DR)),
              ncv_exceptions=dict(file="NCV_EXCEPTIONS.csv", sha256=sha256(DEMAND_DIR / "NCV_EXCEPTIONS.csv")),
              dictionary_extension=dict(file="SDMX_DICTIONARY_EXTENSION.json", sha256=sha256(SRC / "SDMX_DICTIONARY_EXTENSION.json")),
              household_gasoline_mwh=gas)
    write_json_i1(ev, EVIDENCE)
    return ev


def main():
    p = argparse.ArgumentParser(); p.add_argument("--gates", action="store_true"); a = p.parse_args()
    if a.gates:
        print(json.dumps(gates(), indent=1)); return
    ev = build_sdmx_base()
    print(json.dumps(dict(capsule=ev["capsule"], base=ev["base"], blend_memo=ev["blend_memo"], household_gasoline_mwh=ev["household_gasoline_mwh"]), indent=1))


if __name__ == "__main__":
    main()
