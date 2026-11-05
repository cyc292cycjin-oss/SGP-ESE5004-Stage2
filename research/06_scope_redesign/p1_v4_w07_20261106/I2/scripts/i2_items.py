"""I2 item definitions: one rule set for all eleven countries (instruction section 2.3; decisions 203-210). Every physical input is taken from
the W07 session deliverables (read only) and re-evaluated in the I2 chain on the SDMX base; the rules that differ from a session's main path
are listed in RULE_DIFFERENCES (and in REPORT.md section 2).

Units: MWh, t. 2050 vectors use the carrier keys of v3_industry.CARRIERS.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i2_common as cm  # noqa: E402

I1CODE = cm.SCRATCH / "i1code" / "scripts"
CHEM = "chemical and petrochemical"
NMM = "non-metallic minerals"
PAPER = "paper pulp and print"
SUBTX = {"1211": "iron and steel", "1213": CHEM, "1214A": "non-ferrous metals", "1214B": NMM, "1214C": "transport equipment", "1214D": "machinery",
         "1214E": "mining and quarrying", "1214F": "food and tobacco", "1214G": PAPER, "1214H": "wood and wood products", "1214I": "construction",
         "1214J": "textile and leather", "1214O": "other"}
# decision 210 item 4: self-produced residues (a) - bagasse, black liquor in every industry row; 'other vegetal material and residues' (5150) in
# food, wood, paper and (I2 reading, INFERENCE: rice husk at rice mills, G4 MM item 4) the n.e.s. row; 5150 elsewhere (NMM, chemicals, textile)
# is purchased biomass (c) and stays
RESIDUE_A = {"5120": "all", "5140": "all", "5150": {"1214F", "1214G", "1214H", "1214O"}}
FW_CODE = "5110"
ID_FW_MEAN_KM3 = 29510.0          # UNSD fuelwood n.e.s. industry, 2010-2017 mean, thousand m3 (S2 section 3; G0 step 8; decision 206)
BL_GJ_T = 22.0                    # ETSAP chemical pulp black liquor (S2 / G3)
HVC_C1 = 3.2688016662080988       # JRC-IDEES 2019 energy use per t HVC, S2 convention (I1 HVC_VECTOR_CHECK.csv)
HVC_C2 = 5.190822737636671        # decision 210 item 5: consistent 2019 energy use (ETSAP SMR fuel part only)
HVC_EL_SHARE_C1 = 1.0 / 12.0      # ETSAP BAT olefins electricity share (S2 / G3 ETH_EL_SHARE), electricity per t unchanged under (c2)
HVC_VEC_B = {"electricity": 2.45374975383589, "heat": 0.18189882191578263, "gas": 3.29468660533621 - 1.47568072194036, "hydrogen": 0.17266107692307692}   # (b) 4.627
HVC_VEC_A = {"electricity": 2.45374975383589, "heat": 0.18189882191578263, "gas": 3.29468660533621, "hydrogen": 0.17266107692307692}                         # (a) 6.103
MEOH_GAS_PER_T = 4.777777778      # G1 Labuan energy-use intensity (PyPSA-Eur today 10.25 - ETSAP feedstock 5.47 MWh CH4/t)
MEOH_EL_PER_T = 0.167
CEMENT_USGS_2019_T = {"ID": 71.9e6, "MY": 16.102e6, "VN": 105.533e6, "TH": 40.261e6, "PH": 27.7e6, "MM": 5.1e6, "KH": 7.4e6, "LA": 5.208e6, "BN": 0.1e6}
METHANOL_DROP = ["BN", "ID", "MM", "PH", "SG", "TH", "VN"]    # every country with an s3_0 EU27-weight methanol load (I1 tables/I1_3_METHANOL_LOAD_CHECK.csv)


def vz() -> dict:
    return {k: 0.0 for k in cm.OUTC}


def vec(d: dict, scale: float = 1.0) -> dict:
    out = vz()
    for k, x in d.items():
        out[k] = out.get(k, 0.0) + float(x) * scale
    return out


def growth(cc: str, base_year: int) -> float:
    """S0 R2 / v3 product rule: G^((2050 - y_b) / 28 x 0.5), G = AEO8 D.2 real GDP 2050 / 2022 (INDUSTRY_OUTPUT_2050_M08B.csv)."""
    r = pd.read_csv(cm.DEMAND / "INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country")
    return float(r.at[cc, "gdp_growth_2022_2050"]) ** ((2050 - base_year) / 28.0 * 0.5)


# ======================================================================================================== SDMX tables (S5p conversion)
def i1code():
    if str(I1CODE) not in sys.path:
        sys.path.insert(0, str(I1CODE))
    import i1_base as ib   # noqa: E402  (I1 code copied to the scratch folder by i2_base.py; REPO = I2 worktree)
    import reconstruct_base_accounts as rba   # noqa: E402
    return ib, rba


def sdmx_industry_cells() -> pd.DataFrame:
    """Energy (MWh, S5p conversion: SDMX factors, ID hard coal 20.29, ID coke 28.20) of every industry record by country x transaction x commodity
    (carrier from the extended dictionary); coal children replaced by parents per transaction (repository rule)."""
    ib, rba = i1code()
    conv = ib.ext_conversion(json.loads((cm.SRC / "FROZEN_UPSTREAM_CONVERSIONS.json").read_text()))
    cap = json.loads((cm.SCRATCH / "SDMX_2019_CAPSULE.json").read_text())["records"]
    R = ib.Recon(dict(records=cap), conv, "d207")
    rows = []
    for c in cm.ASEAN:
        for t in list(SUBTX) + ["121"]:
            rs = [r for r in R.rows if r["Country"] == c and r.get("TransactionCode") == t]
            el = [r for r in rs if R.fuels.get(rba.commodity(r["Commodity"])) == "electricity"]
            fu = [r for r in rs if R.fuels.get(rba.commodity(r["Commodity"])) in ("oil", "gas", "coal", "biomass")]
            fu, _ = R.select_coal_hierarchy(fu)
            for r in el:
                rows.append(dict(country=c, tx=t, sub=SUBTX.get(t, "total"), code=r["CommodityCode"], commodity=r["Commodity"], carrier="electricity",
                                 unit=r["Unit"], quantity=float(r["Quantity"]), mwh=float(r["Quantity"]) * 1000.0, factor=""))
            for r in fu:
                rows.append(dict(country=c, tx=t, sub=SUBTX.get(t, "total"), code=r["CommodityCode"], commodity=r["Commodity"], carrier=R.fuels[rba.commodity(r["Commodity"])],
                                 unit=r["Unit"], quantity=float(r["Quantity"]), mwh=float(R.convert(r)[0]), factor=r.get("CONVERSION_FACTOR", "")))
    return pd.DataFrame(rows)


def build_cache(cells: pd.DataFrame, drop: set | None = None, scale: dict | None = None) -> dict:
    """Industry sub-sector cache (MWh; s3_0 uses within-carrier shares) from the SDMX cells (I1 i1_chain.sdmx_cache rule: 'other' = 1214O + the
    positive residual of 121 minus its reported children). drop: {(country, code, tx)} records removed from the sub-row AND from the 121 total;
    scale: {(country, code): factor} applied to the sub-rows and the 121 total of that commodity."""
    drop, scale = drop or set(), scale or {}
    subs = sorted(set(SUBTX.values()))
    E = {c: {car: {s: 0.0 for s in subs} for car in cm.CARS19} for c in cm.ASEAN}
    tot = {c: {car: 0.0 for car in cm.CARS19} for c in cm.ASEAN}
    for r in cells.itertuples():
        f = scale.get((r.country, r.code), 1.0)
        if r.tx != "121" and (r.country, r.code, r.tx) in drop:
            continue
        v = r.mwh * f
        if r.tx == "121":
            v -= sum(cells[(cells.country == r.country) & (cells.code == r.code) & (cells.tx == t2)].mwh.sum() * f for (c2, k2, t2) in drop if c2 == r.country and k2 == r.code)
            tot[r.country][r.carrier] += v
        else:
            E[r.country][r.carrier][SUBTX[r.tx]] += v
    for c in cm.ASEAN:
        for car in cm.CARS19:
            res = tot[c][car] - sum(E[c][car].values())
            if res > 1e-6:
                E[c][car]["other"] += res
    recs = [dict(country=c, carrier=car, **{s: repr(v) for s, v in E[c][car].items()}) for c in cm.ASEAN for car in cm.CARS19]
    return dict(source="I2 rebuild from UNSD SDMX 2019 (W12 responses), S5p conversion", source_sha256="", source_year=2019,
                meaning="MWh by industry sub-sector (shares only in s3_0); other = 1214O + positive residual of 121", numeric_acceptance="I2_SCRATCH", records=recs)


def residues(cells: pd.DataFrame) -> pd.DataFrame:
    """Decision 210 item 4 (a): self-produced residues in the 2019 industry rows (MWh, S5p), and the purchased biomass kept (c)."""
    z = cells[(cells.tx != "121") & cells.code.isin(["5120", "5140", "5150"])].copy()
    def cls(r):
        rule = RESIDUE_A[r.code]
        return "a" if (rule == "all" or r.tx in rule) else "c"
    z["cls"] = z.apply(cls, axis=1)
    return z


# ======================================================================================================== session inputs
def load_sessions() -> dict:
    W = cm.W07
    S = {}
    S["s2_chain"] = json.loads((cm.S2D / "s2/_products_evidence.json").read_text())["extra"]["chain_inputs"]
    S["g1_ci"] = json.loads((W / "G1/tables/_products_evidence.json").read_text())["extra"]["chain_inputs"]
    S["g1_num"] = {x["key"]: x["value"] for x in json.loads((W / "G1/tables/_products_evidence.json").read_text())["numbers"]}
    S["g2_ci"] = json.loads((W / "G2/evidence/_chain_inputs.json").read_text())
    S["g3_p"] = json.loads((W / "G3/tables/_products_inputs.json").read_text())
    S["g3_cap"] = json.loads((W / "G3/tables/_captive_inputs.json").read_text())
    S["g4_ci"] = json.loads((W / "G4/evidence/_chain_inputs.json").read_text())
    cap = pd.read_csv(cm.S2D / "s1/ID_CAPTIVE_COAL_2019.csv"); tot = cap[cap.group == "合计"].set_index("level")
    S["id_captive"] = {lv: dict(C_kt=float(tot.at[lv, "coal_in_industry_kt"]), E_mwh=float(tot.at[lv, "gen_in_industry_gwh"]) * 1e3) for lv in ("low", "central", "mid", "high")}
    eth = pd.read_csv(W / "G2/tables/VN_ETHYLENE_SENS.csv") if (W / "G2/tables/VN_ETHYLENE_SENS.csv").exists() else None
    S["vn_eth"] = eth
    ev = {x["key"]: x["value"] for x in json.loads((W / "G2/evidence/_unsd_evidence.json").read_text())["numbers"]}
    S["vn_el_rows"] = {"iron and steel": ev["unsd.el_row_2019_backcast.iron_and_steel"] * 1e6, CHEM: ev["unsd.el_row_2019_backcast.chemical_and_petrochemical"] * 1e6}
    return S


# ---- pulp and paper: one rule (G3 g3_products: FAOSTAT x JRC-IDEES today with the PyPSA-Eur structure; black liquor of chemical + dissolving
#      pulp x 22 GJ/t capped at the fuel part, outside T_v2; the rest of the fuel (incl. the purchased biomass) is purchased) ------------------
def pp_tables() -> dict:
    W = cm.W07
    t = {"ID": pd.read_csv(cm.S2D / "s2/ID_PULP_PAPER_FAOSTAT.csv"), "MY": pd.read_csv(W / "G1/tables/MY_PULP_PAPER_FAOSTAT.csv"),
         "VN": pd.read_csv(W / "G2/tables/VN_PULP_PAPER_FAOSTAT.csv"), "TH": pd.read_csv(W / "G3/tables/TH_PULP_PAPER_FAOSTAT.csv"),
         "PH": pd.read_csv(W / "G3/tables/PH_PULP_PAPER_FAOSTAT.csv")}
    g4 = pd.read_csv(W / "G4/evidence/PULP_PAPER_FAOSTAT_G4.csv")
    for cc in ("MM", "LA"):
        t[cc] = g4[g4.iso == cc].copy()
    return t


def ratios():
    r50 = pd.read_csv(cm.REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0)
    tday = pd.read_csv(cm.REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv").set_index("sector")
    return r50, tday


RATIO_TO_OUT = {"elec": "electricity", "coal": "coal", "coke": "coal", "biomass": "biomass", "methane": "gas", "hydrogen": "hydrogen", "heat": "heat", "ammonia": "ammonia", "methanol": "methanol"}


def vec2050(sector: str, t: float) -> dict:
    r50, _ = ratios(); out = vz()
    for k, oc in RATIO_TO_OUT.items():
        out[oc] += float(r50.at[k, sector]) * t
    return out


def today_vec(sector: str, t: float) -> dict:
    r50, tday = ratios(); cars = ("elec", "coal", "coke", "methane", "biomass", "hydrogen", "heat")
    col = r50[sector]; tf = float(sum(col[c] for c in cars)); T = float(tday.at[sector, "today_total_mwh_per_t"])
    return {c: float(col[c]) / tf * T * t for c in cars}


def pp_item(cc: str, tab: pd.DataFrame, part: str = "existing") -> dict | None:
    """Unified pulp and paper item (leaf FAOSTAT items of the session tables; columns group / item / q_2019_t / q_2050_main_t, G4: q_2050_t).
    part 'existing': items with 2019 output (2019 deduction + 2050); 'new': lines with no 2019 output and a 2050 output (e.g. the LA paper line of
    2021; decision 208: operating in the latest status year -> main), 2050 only; 'all': both."""
    T = tab.copy()
    q19 = "q_2019_t"; q50 = "q_2050_main_t" if "q_2050_main_t" in T.columns else "q_2050_t"
    T[q19] = pd.to_numeric(T[q19], errors="coerce").fillna(0.0); T[q50] = pd.to_numeric(T[q50], errors="coerce").fillna(0.0)
    new = (T[q19] <= 0) & (T[q50] > 0)
    T = T[~new] if part == "existing" else (T[new] if part == "new" else T)
    if T.empty or (T[q19].sum() <= 0 and T[q50].sum() <= 0):
        return None
    chem = T["item"].str.startswith("Chemical wood pulp") | (T["item"] == "Dissolving wood pulp")
    tot = T.groupby("group")[[q19, q50]].sum()
    e19 = {g: today_vec("Pulp production" if g == "pulp" else "Paper production", float(tot.at[g, q19])) for g in tot.index if g in ("pulp", "paper")}
    el19 = sum(v["elec"] for v in e19.values()); tot19 = sum(sum(v.values()) for v in e19.values())
    bl19 = min(float(T.loc[chem, q19].sum()) * BL_GJ_T / 3.6, tot19 - el19)
    v = vz()
    for g in tot.index:
        if g in ("pulp", "paper"):
            for k, x in vec2050("Pulp production" if g == "pulp" else "Paper production", float(tot.at[g, q50])).items():
                v[k] += x
    bl50 = min(float(T.loc[chem, q50].sum()) * BL_GJ_T / 3.6, v["biomass"])
    v_ex = dict(v); v_ex["biomass"] -= bl50
    return dict(name=("pulp_paper_new" if part == "new" else "pulp_paper"), row=PAPER, fuel19=tot19 - el19 - bl19, el19=el19, v2050=v_ex, closed_loop_bl19=bl19, closed_loop_bl50=bl50,
                full2050=sum(v.values()), q19=float(tot[q19].sum()), q50=float(tot[q50].sum()))


# ---- HVC (decision 210 item 5: 2019 deduction 5.191, 2050 4.627 vector (b); S2 pair 3.269 / 6.103 as sensitivity) ------------------------------
def hvc_items(S: dict, basis: str = "i2") -> dict:
    """{cc: dict(hvc19_t, hvc50_base_t (2019 plants), hvc50_new_t (new plants, 5g), row, fuel_split)}."""
    g3 = S["g3_p"]; g1 = S["g1_ci"]
    out = {}
    id19 = 860000.0 * 0.85 * 1.697
    out["ID"] = dict(hvc19_t=id19, hvc50_base_t=id19 * growth("ID", 2019), hvc50_new_t=1860000.0 * 0.85 * 1.697 * growth("ID", 2025) - id19 * growth("ID", 2019),
                     row=CHEM, fuel_split=None, src="G0 / S2: Chandra Asri 860 kt (2019) + LINE 1,000 kt (2025), u 0.85, HVC/ethylene 1.697")
    for cc in ("TH", "PH", "SG"):
        c0 = g3[cc]["ethylene"]["cases"]["main|central"]; cn = g3[cc]["ethylene"]["cases"]["base_2020_incl_new|central"]
        new = (cn["hvc_2050_t"] - c0["hvc_2050_t"]) if cc == "TH" else 0.0
        out[cc] = dict(hvc19_t=c0["hvc_t"], hvc50_base_t=c0["hvc_2050_t"], hvc50_new_t=new, row=CHEM, fuel_split=None,
                       src=f"G3 _products_inputs.json {cc} ethylene main|central" + (" + Cracker No 5 (base_2020_incl_new)" if cc == "TH" else ""))
    m = g1["chem_moves_2019"]["central"]
    my19 = sum(m[p][c] for p in ("olefins", "aromatics") for c in ("gas", "electricity")) / HVC_C1
    my50 = sum(g1["chem_2050"]["central"]["hvc"].values()) / sum(HVC_VEC_A.values())
    pic50 = sum(g1["chem_2050_r4"]["pic_2025"].values()) / sum(HVC_VEC_A.values())
    out["MY"] = dict(hvc19_t=my19, hvc50_base_t=my50, hvc50_new_t=pic50, row=None, fuel_split={"gas": 1.0},
                     src="G1 chain inputs: Titan + Kerteh olefins and aromatics (fuel from 'other' gas, NEB); PIC Pengerang 2025 (R4 -> main)")
    e = S["vn_eth"]; vn50_t = float(e[e.level == "central"].hvc_2050_t.iloc[0])
    out["VN"] = dict(hvc19_t=0.0, hvc50_base_t=0.0, hvc50_new_t=vn50_t, row=CHEM, fuel_split=None, src="G2 VN_ETHYLENE_SENS.csv central: Long Son 950 kt (2023) x 0.85, R4 -> main")
    for cc, d in out.items():
        e_t = (HVC_C2 if basis == "i2" else HVC_C1)
        el_t = HVC_C1 * HVC_EL_SHARE_C1
        d["el19_per_t"] = el_t; d["fuel19_per_t"] = e_t - el_t
        d["vec"] = HVC_VEC_B if basis == "i2" else HVC_VEC_A
    return out


# ---- methanol (decision 210 item 7) ------------------------------------------------------------------------------------------------------------
def methanol_items(S: dict) -> dict:
    g1 = S["g1_ci"]; n = S["g1_num"]
    out = {}
    out["MY"] = dict(name="methanol", row=None, fuel19=n["products.chem.methanol.central.deduct_gas_2019_mwh"] * 1e6, el19=n["products.chem.methanol.central.deduct_el_2019_mwh"] * 1e6,
                     fuel_split={"gas": 1.0}, v2050=vec(g1["chem_2050"]["central"]["methanol"]), src="G1 Labuan 2,330 kt x 0.85, energy use only")
    for cc, cap in (("ID", 660000.0), ("BN", 850000.0)):
        t19 = cap * 0.85; t50 = t19 * growth(cc, 2019)
        out[cc] = dict(name="methanol", row=CHEM, fuel19=t19 * MEOH_GAS_PER_T, el19=t19 * MEOH_EL_PER_T, fuel_split=None,
                       v2050=vec({"gas": MEOH_GAS_PER_T * t50, "electricity": MEOH_EL_PER_T * t50}),
                       src=f"GEM GCT 2026-11 operating capacity {cap / 1e3:.0f} kt x 0.85; G1 energy-use intensity (gas {MEOH_GAS_PER_T:.4f}, electricity {MEOH_EL_PER_T} MWh/t)")
    out["MY_new"] = dict(v2050=vec(g1["chem_2050_r4"]["sarawak_petchem_2023"]), src="G1: Sarawak Petchem 1,750 kt (2023), R4 -> main")
    return out


# ---- other items ---------------------------------------------------------------------------------------------------------------------------
def other_items(S: dict) -> dict:
    g1, g2, g3, g4 = S["g1_ci"], S["g2_ci"], S["g3_p"], S["g4_ci"]
    it = {}
    it["glass"] = {"VN": dict(name="glass", row=NMM, fuel19=g2["glass_2019"]["fuel"], el19=g2["glass_2019"]["electricity"], v2050=vec(g2["glass_2050"]))}
    for cc in ("TH", "PH", "SG"):
        g = g3[cc]["glass"]; it["glass"][cc] = dict(name="glass", row=NMM, fuel19=g["fuel19"], el19=g["el19"], v2050=vec(g["v2050"]))
    it["alumina"] = {"VN": dict(name="alumina", row=None, fuel19=g2["alumina_2019"]["fuel"], el19=g2["alumina_2019"]["electricity"], v2050=vec(g2["alumina_2050"]))}
    it["copper"] = {}
    for p, cc, row in (("MM_copper", "MM", "non-ferrous metals"), ("LA_copper", "LA", None)):
        d = g4["products"][p]; it["copper"][cc] = dict(name="copper", row=row, fuel19=d["e2019_purchased_fuel"], el19=d["e2019_purchased_el"], v2050=vec(d["v2050_counted"]))
    it["lime"] = {"MY": dict(name="lime", row=None, fuel19=g1["lime_2019"]["fuel"], el19=g1["lime_2019"]["electricity"], v2050=vec(g1["lime_2050"]))}
    m = g1["chem_moves_2019"]["central"]["ammonia"]
    it["my_ammonia_dup"] = [("MY", "other", "gas", m["gas"]), ("MY", "other", "electricity", m["electricity"])]
    return it


RULE_DIFFERENCES = [
    dict(item="2019 base", rule="UNSD SDMX current database for every country (decision 210 item 1); SDMX factors, ID hard coal 20.29, ID coke 28.20",
         differs_from="G2 VN fuelwood (export 14,725 thousand m3 kept as main) and G4 MM fuelwood / bagasse (export values kept)",
         reason="one base version for all countries; the export values become sensitivities (G2 / G4 recommended the export value only because the base was the export)"),
    dict(item="self-produced residues", rule="bagasse, black liquor and 5150 in food / wood / paper / n.e.s. rows out of demand and potential in every country (210 item 4 a)",
         differs_from="G0 (bagasse kept in T_v2), G4 (MM / LA bagasse kept), G2 (VN bagasse kept); G3 already removed TH / PH bagasse",
         reason="decision 210 item 4 supersedes decision 208 item 1 and the 'reported -> keep' reading of 206 item 3"),
    dict(item="pulp and paper", rule="FAOSTAT x JRC-IDEES today (PyPSA-Eur structure); black liquor of chemical + dissolving pulp x 22 GJ/t capped at the fuel part, outside T_v2; all other fuel incl. biomass purchased; 2019 deduction from the paper row, excess from 'other', rest recorded",
         differs_from="G0 ID (non-biomass 2019 fuel 0.66 TWh kept as purchased; same 2050), G1 MY (all biomass outside T_v2), G3 TH / PH (2019 deduction capped at the paper row), G4 MM (paper biomass outside T_v2)",
         reason="one rule: only own black liquor is self-produced (210 item 4 a); recovered-fibre mills buy their steam fuel (G1 decision 5, G4 MM item 7); the row cap of G3 is replaced by the general S0 3.2 rule (row, then other, then D163-4)"),
    dict(item="HVC", rule="2019 deduction 5.191 MWh/t (electricity 0.272, fuel 4.918), 2050 vector (b) 4.627 MWh/t (decision 210 item 5)",
         differs_from="G0-G3 (3.269 / 6.103)", reason="decision 210 item 5"),
    dict(item="new plants", rule="plants operating in the latest status year are main: ID LINE, MY PIC and Sarawak Petchem methanol, VN Long Son, TH Cracker No 5, LA paper line (2021); SG without GEPDSGP0004",
         differs_from="G1 / G2 / G3 (R4 sensitivity), G4 (LA paper line sensitivity)", reason="decision 208 (new plants), applied to every country including the LA paper line"),
    dict(item="methanol", rule="EU27-weight methanol load of the chemicals row dropped in BN, ID, MM, PH, SG, TH, VN (DFX F2 precedent); explicit energy use for MY (Labuan, Sarawak), ID (Kaltim 660 kt) and BN (850 kt) at the G1 intensity",
         differs_from="all sessions (methanol load kept); BN chemicals not counted (G4, decision 202 item 4)", reason="decision 210 item 7"),
    dict(item="nickel", rule="2023 base, Wei Case 3 for every product (decision 208)", differs_from="G0 main (NPI Case 4)", reason="decision 208"),
    dict(item="growth readings", rule="SDMX base and (ii) corrections under IId; (i) corrections (captive coal) and items outside the national balance (ID fuelwood) under reading I",
         differs_from="G0-G4 (reading I for everything)", reason="decision 210 items 2-4"),
    dict(item="ID industrial fuelwood", rule="2010-2017 mean (29,510 thousand m3) outside the anchor, reading-I growth (210 item 4 b)", differs_from="G0 (inside the anchor, reading I)", reason="decision 210 item 4 b"),
    dict(item="VN decomposition", rule="hybrid split; T_v2 and decomposition from the same run (decision 208)", differs_from="G2 main (v3 two-run rule)", reason="decision 208"),
]
