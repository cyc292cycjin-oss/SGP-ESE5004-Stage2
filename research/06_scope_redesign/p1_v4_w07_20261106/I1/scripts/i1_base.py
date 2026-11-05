"""I1-1b: rebuild the 2019 base year (11 countries, all sectors, all commodities) from the UNSD SDMX current database with the model's own
account mapping, and decompose the difference to the current base (UNdata web export 2025-05-02) into four classes.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i1_base.py

Same code path as the repository: research_inputs/assembly_v1/sources -> reconstruct_base_accounts.Reconstruction (account mapping,
parent-replaces-children coal rule, alias de-duplication, rail parent + RailNonElectric child) -> D1 base rows as in d1_demand_2050.py
main() lines 166-200 (accounts, ASSEMBLY_V1_BLEND_BASELINE overrides, electricity.json by sector, non-energy reference, BN/KH/LA/TL
marine-bunker EB override). The repository modules are imported read-only; nothing in the repository is written.

Reproduction gates (stop if they fail):
  G1  reconstruct(sources) == research_inputs/.../BASE_RECONSTRUCTION.json (every account value and status, string-exact);
  G2  D1 base rows assembled here == base_2019_mwh of DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv (every row, float-exact);
  G3  the generalised blend rule used for the SDMX versions, applied to the unchanged capsule, gives the same D1 base rows (G2 rows).
Generalised blend rule (= the two rules in force): for each biofuel row (Biodiesel / Biogasoline / Bio jet kerosene) in an account that also
has the petroleum peer, the petroleum energy is reduced by Z x (petroleum NCV), Z = the 'Of which' memo quantity of the same country and
transaction when UNSD publishes one (COMPATIBLE_BLEND_EVIDENCE rule), else the whole biofuel quantity (maximum-overlap baseline A).

Steps (each a full rebuild; the class of a difference is the step that introduces it):
  S0  current base (export capsule, TH road overlay, v3 frozen factors)                        = repository
  S1  + export truncation: SDMX rows for (country, commodity) cut off by a 100,000-row export file
  S2  + commodities absent from every export file (SDMX rows; extended dictionary; SDMX factor, no frozen factor exists)
  S3  all quantities from SDMX (data version: revised values, flows added / removed), frozen factors where they exist
  S4  SDMX CONVERSION_FACTOR for every mass / volume row (NCV difference)                     = new base BASE2019_SDMX
  S5  S4 with the decision-207 coal NCV where it differs from SDMX (ID hard coal 20.29 GJ/t)  = option, not a class
Writes BASE2019_SDMX/*, BASE2019_DIFF.csv, tables/I1_1_*.csv, evidence/I1_1b_base.json.
"""
from __future__ import annotations

import copy
import json
import sys
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i1_common as cm  # noqa: E402
import reconstruct_base_accounts as rba  # noqa: E402  (repository module, read only)
from d1_common import SRC_DIR, fmt  # noqa: E402
from d1_demand_2050 import ACCOUNT_SECTOR, BUNKER_EB_CSV, NONENERGY_CARRIER, SECTORS, electricity_by_sector  # noqa: E402

BIO_PEER = {"biodiesel": "gas oil/ diesel oil", "biogasoline": "motor gasoline", "bio jet kerosene": "kerosene-type jet fuel"}
MEMO_CODE = {"biodiesel": "5222", "biogasoline": "5212", "bio jet kerosene": "5232"}
NEW_FUELS = {"biomass_fuels": ["Other Vegetal Material and Residues", "Other liquid biofuels"],
             "oil_fuels": ["Other oil products n.e.c.", "White spirit and special boiling point industrial spirits"],
             "coal_fuels": ["Other recovered gases", "Other coal products"]}
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
D207_COAL = {("ID", "hard coal"): D("20.29")}      # decision 207 item 2 (G0 main); every other decision-207 coal value equals the SDMX factor
TX_CODE_ACCOUNT = {"1221": "RoadResidualFuel", "1222": "TransportEmbeddedFuelParent", "121": "IndustryFinalEnergy", "1235": "ServicesFuel",
                   "1232": "AgricultureFinalEnergy", "1231": "ResidentialFuel", "1223": "DomesticAviationFuel", "1224": "DomesticShippingFuel",
                   "1225": "TransportNEC", "1234": "OtherNEC"}


class Recon(rba.Reconstruction):
    """Repository reconstruction with a factor switch: 'frozen' (v3 upstream factors; SDMX factor only for commodities without a frozen
    factor), 'sdmx' (SDMX CONVERSION_FACTOR for every mass / volume row), 'd207' (as 'sdmx' but decision-207 coal NCVs)."""

    def __init__(self, source, conversion, mode="frozen"):
        self.mode = mode
        super().__init__(source, conversion)

    def convert(self, r):
        c = rba.commodity(r["Commodity"]); unit = r["Unit"]; f = self.fuels.get(c)
        cf = r.get("CONVERSION_FACTOR") or ""
        if unit in ("Metric tons,  thousand", "Cubic metres, thousand") and f not in (None, "electricity"):
            new_com = c not in self.factors
            if self.mode in ("sdmx", "d207") or new_com:
                if self.mode == "d207" and (r["Country"], c) in D207_COAL:
                    cf = str(D207_COAL[(r["Country"], c)])
                if cf:
                    q = rba.decimal(r["Quantity"])
                    return q * D(cf) * 1000 / D("3.6"), f"{unit} x SDMX CONVERSION_FACTOR {cf} GJ/unit x 1000 / 3.6", \
                        ("NCV_DECISION_207" if self.mode == "d207" and (r["Country"], c) in D207_COAL else "NCV_SDMX_CONVERSION_FACTOR")
                if new_com:
                    raise ValueError("No frozen factor and no SDMX factor: " + c)
        return super().convert(r)


def ext_conversion(conv: dict) -> dict:
    c = copy.deepcopy(conv)
    for k, names in NEW_FUELS.items():
        c["constants"][k] = list(c["constants"][k]) + names
    return c


def rail_children(result: dict) -> None:
    """reconstruct_base_accounts.py lines 225-234 (rail parent kept as accounting, carrier children added)."""
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
    """Generalised blend rule (module docstring). memo: (country, memo code, account) -> Decimal quantity (thousand t).
    Works on the selected rows (petroleum row MWh reduced) and on the account values / carrier breakdowns."""
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
                # oil accounts only: the rail parent (unclassified_fuel) keeps its raw sum, as in the repository (it is never blend-resolved)
                if a["Country"] == c and p["RowID"] in a["SourceRows"] and a["Carrier"] == "oil":
                    a["ValueMWh"] = str(D(a["ValueMWh"]) - cut)
                    a["CarrierBreakdownMWh"]["oil"] = str(D(a["CarrierBreakdownMWh"]["oil"]) - cut)
                    a["BlendRule"] = rule
                if a["Country"] == c and (p["RowID"] in a["SourceRows"] or b["RowID"] in a["SourceRows"]) and a["Status"] == "UNRESOLVED_BIOFUEL_OVERLAP":
                    a["Status"] = "NUMERIC_INPUT_READY"; a["Classification"] = "REQUIRED_PHYSICAL"; a["Reason"] = "blend resolved: " + rule
            log.append(dict(step=label, country=c, account=acc, bio=b["Commodity"], petroleum=p["Commodity"], P_kt=str(P), B_kt=str(B), Z_kt=str(Z),
                            rule=rule, petroleum_mwh_cut=str(cut)))


def d1_rows(result: dict, elec_records: list, blend_baseline: dict | None, eb: dict) -> pd.DataFrame:
    """d1_demand_2050.py main() lines 166-200, base columns only."""
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
    for c in cm.ASEAN:
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


def commodity_rows(result: dict, elec_records: list, step: str) -> pd.DataFrame:
    """Commodity-level energy per country x account (selected rows after blend; electricity by sector; non-energy rows)."""
    out = []
    for r in result["selected_rows"]:
        out.append(dict(step=step, country=r["Country"], account=r["Account"], sector=ACCOUNT_SECTOR[r["Account"]], carrier=r["Carrier"],
                        commodity=rba.commodity(r["Commodity"]), mwh=float(r["MWh"])))
        if r.get("OriginalParentAccount"):   # rail rows count in the parent account and in the RailNonElectric child (both in D1)
            out.append(dict(step=step, country=r["Country"], account=r["OriginalParentAccount"], sector="Transport", carrier="unclassified_fuel",
                            commodity=rba.commodity(r["Commodity"]), mwh=float(r["MWh"])))
    es = electricity_by_sector(elec_records)
    for c in cm.ASEAN:
        for s in SECTORS:
            out.append(dict(step=step, country=c, account="UNSD_electricity_" + s, sector=s, carrier="electricity", commodity="electricity", mwh=es[c][s]))
    for ne in result["nonenergy_reference"]:
        out.append(dict(step=step, country=ne["Country"], account="NonEnergy:" + ne["Commodity"], sector="NonEnergyUse",
                        carrier=NONENERGY_CARRIER.get(ne["Commodity"], NEU_EXTRA.get(ne["Commodity"])), commodity=rba.commodity(ne["Commodity"]), mwh=float(ne["MWh"])))
    return pd.DataFrame(out)


NEU_TX = {"non-energy uses", "consumption for non-energy uses"}
DROPPED_NEU: list = []
ZERO_PROOF_ERRORS: list = []


class ZeroScope(Recon):
    """Zero proofs (status only; the D1 value of an account without candidates is 0 either way). The repository bounds them to ONE source
    version (reconstruct(): the original export capsule, never the TH road overlay); a proof that meets mixed source versions is not
    possible and is recorded instead of raising."""

    def reported_zero_bound(self, c, account, fuel):
        try:
            return super().reported_zero_bound(c, account, fuel)
        except ValueError as exc:
            ZERO_PROOF_ERRORS.append(dict(country=c, account=account, fuel=fuel, error=str(exc)))
            return None


def build_version(records: list, conv: dict, mode: str, memo: dict, log: list, label: str, zero_records: list | None = None) -> dict:
    fuels = Recon(dict(records=[]), conv, mode).fuels
    keep = []
    for r in records:   # non-energy rows of commodities outside the fuel dictionary (refinery feedstocks, ...) cannot be converted: listed
        if rba.norm(r["Transaction"]) in NEU_TX and r["Commodity"] and fuels.get(rba.commodity(r["Commodity"])) is None:
            DROPPED_NEU.append(dict(step=label, country=r["Country"], commodity=r["Commodity"], quantity=r["Quantity"], unit=r["Unit"]))
            continue
        keep.append(r)
    src = dict(records=keep)
    rec = Recon(src, conv, mode)
    rec.zero_scope = ZeroScope(dict(records=copy.deepcopy(zero_records if zero_records is not None else keep)), conv, mode)
    res = rec.build()
    rail_children(res)
    blend(res, memo, log, label)
    return res


def export_commodities() -> tuple[set, list]:
    """Commodity names (normalised) present in each of the 52 UNdata export files and the truncated files (exactly 100,000 data rows)."""
    names, trunc = set(), []
    order = sorted(cm.UNSD_NAMES)
    for f in sorted(cm.UNSD_DIR.glob("UNdata_Export_*.txt")):
        data = []
        for ln in f.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
            if not ln.strip():
                break
            data.append(ln)
        coms = {rba.commodity(ln.split('";"')[1].split(" - ")[0]) for ln in data if '";"' in ln}
        names |= coms
        if len(data) == 100000:
            last = data[-1].split('";"')[0].strip('"')
            trunc.append(dict(file=f.name, last_country=last, commodities=sorted(coms), after=[cm.UNSD_NAMES[n] for n in order if n > last]))
    return names, trunc


def main():
    ev = cm.Evidence("I1_1b_base")
    conv = json.loads((cm.SRC / "FROZEN_UPSTREAM_CONVERSIONS.json").read_text())
    convx = ext_conversion(conv)
    blend_bl = {v["BaseAccountID"]: v for v in json.loads((cm.SRC / "ASSEMBLY_V1_BLEND_BASELINE.json").read_text())["records"].values()}
    elec_exp = json.loads((cm.SRC / "electricity.json").read_text())["records"]
    eb = {(r["iso2"], r["flow"]): r for r in pd.read_csv(SRC_DIR / BUNKER_EB_CSV, dtype=str).to_dict("records")}
    repo_base = json.loads((cm.SRC / "BASE_RECONSTRUCTION.json").read_text())
    d1 = pd.read_csv(cm.DEMAND / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", keep_default_na=False)
    key = ["country", "sector", "carrier", "account"]
    if d1.duplicated(key).any():
        raise SystemExit("STOP: duplicate D1 keys " + str(d1[d1.duplicated(key, keep=False)][key].values.tolist()))

    # ---- G1 / G2: repository path -----------------------------------------------------------------------------------
    r0 = rba.reconstruct(cm.SRC)
    acc_repo = {a["AccountID"]: (a["ValueMWh"], a["Status"]) for a in repo_base["accounts"]}
    acc_new = {a["AccountID"]: (a["ValueMWh"], a["Status"]) for a in r0["accounts"]}
    g1 = acc_repo == acc_new
    ev.add("gate.G1_reconstruct_equals_repository", g1, "bool", "VERIFIED", "A", "reconstruct_base_accounts.reconstruct(sources) vs BASE_RECONSTRUCTION.json",
           f"{len(acc_new)} accounts, values and statuses string-exact")
    D0 = d1_rows(r0, elec_exp, blend_bl, eb)
    d1s = pd.read_csv(cm.DEMAND / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", keep_default_na=False, dtype=str)
    m = d1s[key + ["base_2019_mwh"]].merge(D0[key + ["base_2019_mwh"]], on=key, how="outer", suffixes=("_repo", "_i1"), indicator=True)
    m["i1_fmt"] = [fmt(v) if pd.notna(v) else "" for v in m.base_2019_mwh_i1]   # d1_common.write_csv formats every float with fmt()
    g2 = bool((m._merge == "both").all() and (m.base_2019_mwh_repo == m.i1_fmt).all())
    ev.add("gate.G2_d1_base_equals_repository", g2, "bool", "VERIFIED", "A", "D1 rows assembled here vs DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv base_2019_mwh",
           f"{len(m)} rows; unmatched {int((m._merge != 'both').sum())}; string-exact after d1_common.fmt (the repository writer)")
    if not (g1 and g2):
        print(m[(m._merge != "both") | (m.base_2019_mwh_repo != m.i1_fmt)].to_string())
        raise SystemExit("STOP: the unchanged copy does not reproduce the repository base (instruction section 6)")

    # ---- SDMX inputs ------------------------------------------------------------------------------------------------
    cap = json.loads((cm.SCRATCH / "SDMX_2019_CAPSULE.json").read_text())["records"]
    memo_rows = pd.read_csv(cm.BASE_OUT / "SDMX_2019_BLEND_MEMO.csv", dtype=str)
    memo = {(r.country, r.memo_code, TX_CODE_ACCOUNT[r.transaction_code]): D(r.value_raw) for r in memo_rows.itertuples() if r.transaction_code in TX_CODE_ACCOUNT}
    # memo values already used by the repository (COMPATIBLE_BLEND_EVIDENCE) must equal the SDMX memo
    comp = json.loads((cm.SRC / "COMPATIBLE_BLEND_EVIDENCE.json").read_text())["records"]
    for e in comp:
        mk = (e["memo"]["Country"], e["memo"]["CommodityCode"], TX_CODE_ACCOUNT[e["memo"]["Transaction"]])
        ev.add(f"memo.{mk[0]}.{mk[1]}.{mk[2]}", dict(repository=e["memo"]["Quantity"], sdmx=str(memo.get(mk))), "kt", "VERIFIED", "A",
               "COMPATIBLE_BLEND_EVIDENCE.json vs sdmx memo", f"equal: {D(e['memo']['Quantity']) == memo.get(mk)}")
    elec_sdmx = [{"Country or Area": cm.CC_NAME[r["Country"]], "Commodity - Transaction": ELEC_LABEL[r["TransactionCode"]], "Year": "2019",
                  "Unit": r["Unit"], "Quantity": r["Quantity"], "Quantity Footnotes": r["OBS_STATUS"], "Country": r["Country"]}
                 for r in cap if r["CommodityCode"] == "7000" and r["TransactionCode"] in ELEC_LABEL]

    # ---- G3: generalised blend rule on the unchanged capsule -----------------------------------------------------------
    cap0 = json.loads((cm.SRC / "UNSD_2019_SOURCE_CAPSULE.json").read_text())["records"]
    cap_frozen = copy.deepcopy(cap0)     # zero-proof scope of the export versions (reconstruct(): original capsule only)
    ov = json.loads((cm.SRC / "TH_ROAD_LOCAL_VINTAGE_APPLIED.json").read_text())
    byid = {rba.row_id(r): i for i, r in enumerate(cap0)}
    for e in ov["replacements"]:
        cap0[byid[e["OldRowID"]]] = e["NewRawRow"]
    log: list = []
    S = {}
    S["S0"] = build_version(copy.deepcopy(cap0), conv, "frozen", memo, log, "S0", cap_frozen)
    D0g = d1_rows(S["S0"], elec_exp, None, eb)
    m3 = D0[key + ["base_2019_mwh"]].merge(D0g[key + ["base_2019_mwh"]], on=key, how="outer", suffixes=("_repo", "_gen"), indicator=True)
    dmax = float((m3.base_2019_mwh_repo - m3.base_2019_mwh_gen).abs().max())
    g3 = bool((m3._merge == "both").all() and dmax <= 1e-6)
    ev.add("gate.G3_generalised_blend_reproduces", g3, "bool", "VERIFIED", "A", "generalised blend rule on the unchanged capsule vs G2 rows",
           f"{len(m3)} rows, max |diff| {dmax:.3e} MWh")
    if not g3:
        print(m3[(m3._merge != "both") | ((m3.base_2019_mwh_repo - m3.base_2019_mwh_gen).abs() > 1e-6)].to_string())
        raise SystemExit("STOP: generalised blend rule does not reproduce the repository base")

    # ---- S1-S5 -----------------------------------------------------------------------------------------------------
    exp_names, trunc = export_commodities()
    trunc_pairs = {(cc, com) for t in trunc for cc in t["after"] for com in t["commodities"]}
    sdmx_trunc = [r for r in cap if (r["Country"], rba.commodity(r["Commodity"])) in trunc_pairs]
    cap1 = [r for r in cap0 if (r["Country"], rba.commodity(r["Commodity"])) not in trunc_pairs] + copy.deepcopy(sdmx_trunc)
    missing_coms = sorted({rba.commodity(r["Commodity"]) for r in cap} - exp_names)
    sdmx_missing = [r for r in cap if rba.commodity(r["Commodity"]) in missing_coms]
    cap2 = cap1 + copy.deepcopy(sdmx_missing)
    S["S1"] = build_version(copy.deepcopy(cap1), conv, "frozen", memo, log, "S1", cap_frozen)
    S["S2"] = build_version(copy.deepcopy(cap2), convx, "frozen", memo, log, "S2", cap_frozen)
    S["S3"] = build_version(copy.deepcopy(cap), convx, "frozen", memo, log, "S3")
    S["S4"] = build_version(copy.deepcopy(cap), convx, "sdmx", memo, log, "S4")
    S["S5"] = build_version(copy.deepcopy(cap), convx, "d207", memo, log, "S5")
    elec_of = {"S0": elec_exp, "S1": elec_exp, "S2": elec_exp, "S3": elec_sdmx, "S4": elec_sdmx, "S5": elec_sdmx}
    DR = {s: d1_rows(S[s], elec_of[s], None, eb) for s in S}
    CR = pd.concat([commodity_rows(S[s], elec_of[s], s) for s in S], ignore_index=True)
    for s in S:
        unres = [a for a in S[s]["accounts"] if a["Status"].startswith("UNRESOLVED")]
        ev.add(f"{s}.unresolved_accounts", [dict(id=a["AccountID"], value=a.get("ValueMWh"), reason=a["Reason"][:160]) for a in unres], "list", "EXACT", "A",
               f"reconstruction {s}", f"{len(unres)} accounts")

    # ---- D1-level table (country x sector x carrier x account) ----------------------------------------------------------
    W = None
    for s in S:
        x = DR[s].groupby(key, as_index=False).base_2019_mwh.sum().rename(columns={"base_2019_mwh": s})
        W = x if W is None else W.merge(x, on=key, how="outer")
    W = W.fillna(0.0)
    W["d_truncation"] = W.S1 - W.S0; W["d_missing_commodity"] = W.S2 - W.S1; W["d_version"] = W.S3 - W.S2; W["d_ncv"] = W.S4 - W.S3
    W["d_total"] = W.S4 - W.S0; W["d_d207_vs_sdmx"] = W.S5 - W.S4
    st = DR["S4"].set_index(key).base_status
    W["status_S4"] = [st.get(tuple(k), "") for k in W[key].values]
    W = W.sort_values(key)
    cm.write_csv(W.to_dict("records"), cm.BASE_OUT / "BASE2019_SDMX_D1_ROWS.csv")

    # ---- commodity-level diff with classes ----------------------------------------------------------------------------
    ck = ["country", "sector", "account", "carrier", "commodity"]
    P = CR.pivot_table(index=ck, columns="step", values="mwh", aggfunc="sum", fill_value=0.0).reset_index()
    for s in S:
        if s not in P:
            P[s] = 0.0
    classes = [("export_truncation", "S1", "S0"), ("missing_commodity", "S2", "S1"), ("data_version", "S3", "S2"), ("ncv", "S4", "S3")]
    diff = []
    for r in P.itertuples(index=False):
        rd = r._asdict()
        for cls, a, b in classes:
            dv = rd[a] - rd[b]
            if abs(dv) > 1e-6:
                diff.append(dict(**{k: rd[k] for k in ck}, diff_class=cls, delta_mwh=dv, delta_twh=dv / 1e6, base_v3_twh=rd["S0"] / 1e6, base_sdmx_twh=rd["S4"] / 1e6))
    DF = pd.DataFrame(diff)
    DF["in_T_v2_scope"] = DF.sector.eq("Industry")
    DF["energy_use_sector"] = DF.sector.isin(SECTORS)
    cm.write_csv(DF.to_dict("records"), cm.I1 / "BASE2019_DIFF.csv")
    cm.write_csv(P.to_dict("records"), cm.BASE_OUT / "BASE2019_SDMX_COMMODITY_BY_STEP.csv")
    # S4 commodity rows with factor provenance
    sel = []
    for r in S["S4"]["selected_rows"]:
        sel.append(dict(country=r["Country"], account=r["Account"], carrier=r["Carrier"], commodity=r["Commodity"], transaction=r["Transaction"], raw_value=r["RawValue"],
                        raw_unit=r["RawUnit"], mwh=r["MWh"], blend_cut_mwh=r.get("BlendCutMWh", ""), transformation=r["Transformation"], energy_basis=r["EnergyBasis"],
                        source=f"{r['SourceFile']}#{r['PhysicalLine']}", obs_status=r["Footnotes"]))
    cm.write_csv(sel, cm.BASE_OUT / "BASE2019_SDMX_SELECTED_ROWS.csv")
    acc4 = [dict(account_id=a["AccountID"], country=a["Country"], account=a["Account"], carrier=a["Carrier"], value_mwh=a["ValueMWh"], status=a["Status"],
                 energy_basis=a["EnergyBasis"], blend_rule=a.get("BlendRule", ""), source_rows=len(a["SourceRows"]), reason=a["Reason"]) for a in S["S4"]["accounts"]]
    cm.write_csv(acc4, cm.BASE_OUT / "BASE2019_SDMX_ACCOUNTS.csv")
    cm.write_csv([dict(country=c, sector=s, mwh=electricity_by_sector(elec_sdmx)[c][s], method=electricity_by_sector(elec_sdmx)[c]["method"]) for c in cm.ASEAN for s in SECTORS],
                 cm.BASE_OUT / "BASE2019_SDMX_ELECTRICITY_BY_SECTOR.csv")
    cm.write_csv(log, cm.BASE_OUT / "BLEND_RULE_LOG.csv")
    cm.write_csv(DROPPED_NEU, cm.TABLES / "I1_1_NEU_ROWS_WITHOUT_FUEL_GROUP.csv", ["step", "country", "commodity", "quantity", "unit"])
    cm.write_csv(ZERO_PROOF_ERRORS, cm.TABLES / "I1_1_ZERO_PROOF_NOT_POSSIBLE.csv", ["country", "account", "fuel", "error"])
    cm.write_csv([dict(file=t["file"], last_country=t["last_country"], commodities=";".join(t["commodities"]), asean_after_cut=";".join(t["after"])) for t in trunc],
                 cm.TABLES / "I1_1_TRUNCATED_FILES_USED.csv")
    cm.write_csv([dict(commodity=c) for c in missing_coms], cm.TABLES / "I1_1_COMMODITIES_ABSENT_FROM_EXPORT.csv")
    for s in ("S0", "S4", "S5"):
        cm.write_json(dict(step=s, accounts=S[s]["accounts"], nonenergy_reference=S[s]["nonenergy_reference"]), cm.SCRATCH / f"recon_{s}.json")
        DR[s].to_csv(cm.SCRATCH / f"d1_base_{s}.csv", index=False, lineterminator="\n")
    for s in ("S1", "S2", "S3"):
        DR[s].to_csv(cm.SCRATCH / f"d1_base_{s}.csv", index=False, lineterminator="\n")

    # ---- summaries --------------------------------------------------------------------------------------------------
    summ = []
    for c in cm.ASEAN + ["ASEAN11"]:
        d = DF if c == "ASEAN11" else DF[DF.country == c]
        for scope, dd in (("energy_use_5_sectors", d[d.energy_use_sector]), ("industry", d[d.sector == "Industry"]), ("non_energy_use", d[d.sector == "NonEnergyUse"]),
                          ("bunkers", d[d.sector == "InternationalBunkers"])):
            dd = dd[dd.account != "TransportEmbeddedFuelParent"]   # parent and child are both D1 rows; count the child only
            rec = dict(country=c, scope=scope)
            for cls, _, _ in classes:
                rec[f"{cls}_twh"] = float(dd[dd.diff_class == cls].delta_twh.sum())
            rec["total_twh"] = sum(rec[f"{cls}_twh"] for cls, _, _ in classes)
            Wc = W if c == "ASEAN11" else W[W.country == c]
            sec = {"energy_use_5_sectors": Wc.sector.isin(SECTORS), "industry": Wc.sector.eq("Industry"), "non_energy_use": Wc.sector.eq("NonEnergyUse"),
                   "bunkers": Wc.sector.eq("InternationalBunkers")}[scope] & (Wc.account != "TransportEmbeddedFuelParent")
            rec["base_v3_twh"] = float(Wc[sec].S0.sum() / 1e6); rec["base_sdmx_twh"] = float(Wc[sec].S4.sum() / 1e6); rec["base_sdmx_d207_twh"] = float(Wc[sec].S5.sum() / 1e6)
            rec["check_twh"] = rec["base_sdmx_twh"] - rec["base_v3_twh"] - rec["total_twh"]
            summ.append(rec)
    SU = pd.DataFrame(summ)
    cm.write_csv(SU.to_dict("records"), cm.TABLES / "I1_1_DIFF_SUMMARY_BY_COUNTRY_CLASS.csv")
    for r in SU.itertuples():
        ev.add(f"diff.{r.country}.{r.scope}", dict(truncation=r.export_truncation_twh, missing=r.missing_commodity_twh, version=r.data_version_twh, ncv=r.ncv_twh,
                                                   total=r.total_twh, v3=r.base_v3_twh, sdmx=r.base_sdmx_twh, sdmx_d207=r.base_sdmx_d207_twh), "TWh (2019)", "EXACT", "A",
               "BASE2019_DIFF.csv / tables/I1_1_DIFF_SUMMARY_BY_COUNTRY_CLASS.csv", "S0 -> S4 sequential classes; rail parent rows excluded (child counted)")
    top = DF[DF.account != "TransportEmbeddedFuelParent"].assign(a=lambda d: d.delta_twh.abs()).sort_values("a", ascending=False).head(60)
    cm.write_csv(top.drop(columns="a").to_dict("records"), cm.TABLES / "I1_1_DIFF_TOP60.csv")
    p = ev.write()
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 400)
    print("gates G1 G2 G3:", g1, g2, g3, "G3 max diff", dmax)
    print("truncated files:", trunc)
    print("commodities absent from the export:", missing_coms)
    print(SU.round(3).to_string())
    print(top[["country", "sector", "account", "carrier", "commodity", "diff_class", "delta_twh", "base_v3_twh", "base_sdmx_twh"]].round(3).to_string())
    print(pd.DataFrame(log).groupby(["step", "country", "account", "bio", "rule"]).size().to_string())
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
