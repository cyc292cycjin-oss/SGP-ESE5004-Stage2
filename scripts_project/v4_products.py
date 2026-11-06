"""V4 W08 checklist sections 5-7 (decisions 204, 206, 208, 210 items 5 / 7): the v4 product items from the physical input tables of
research_inputs/industry_v4/ (rules moved from the I2 scratch code work/p1_v4_w07_20261106/I2/scripts/i2_items.py, i2_chain.py without change).

    PYTHONHASHSEED=0 python scripts_project/v4_products.py      # writes research_inputs/industry_v4/PRODUCT_ITEMS_V4.csv (review table)

Items (2019 deduction from the same-name UNSD row, then 'other', then recorded (D163-4); 2050 vector added to T_v2 - v4_industry.Chain.deduct / layer):
  captive coal (S4)   CAPTIVE_COAL_2019.csv: moves of tonnes x NCV out of the fuel row, generation into industry electricity (option b, reading I);
  cement (S5b)        CEMENT_USGS_2019.csv: grinding electricity on the USGS 2019 cement tonnes; BN EDGAR 2.A.1 = 0 and 2050 cement electricity only (iii);
  nickel (S5c)        v3_industry.nonferrous(..., 'nf2023'): 2023 base, Wei Case 3 for every product;
  pulp / paper (S5d)  PULP_PAPER_FAOSTAT_V4.csv: FAOSTAT x JRC-IDEES today (PyPSA-Eur structure); black liquor = chemical + dissolving pulp x 22 GJ/t, capped
                      at the fuel part, outside T_v2 (closed loop); every other fuel purchased; 2050 PyPSA-Eur vector minus the black liquor;
  HVC (S5e)           HVC_PLANTS_V4.csv: 2019 deduction 5.191 MWh/t (electricity 0.272), 2050 vector (b) 4.627 MWh/t; utilisation 0.85 in the tonnes;
  methanol (S5f)      METHANOL_PLANTS_V4.csv (+ PRODUCT_DERIVED_INPUTS_V4.csv for MY): energy use 4.778 MWh gas + 0.167 MWh electricity per t; the EU27-weight
                      methanol load of the chemicals row is dropped in BN, ID, MM, PH, SG, TH, VN; BN: no 2019 industry deduction (fuel in UNSD NEU)
                      -> the NEU gas falls by the same energy use (v4_outputs.py);
  new plants (S5g)    HVC_PLANTS_V4.csv hvc50_new_t, the MY Sarawak methanol plant, pulp / paper lines without 2019 output (LA 2021 line): 2050 only;
  S6a                 MY_AMMONIA_FUEL_DUPLICATE.csv: gas 5.546, electricity 0.782 TWh out of 'other' (2019, reading I);
  S6b                 PRODUCT_DERIVED_INPUTS_V4.csv: glass (VN TH PH SG), alumina (VN), copper (MM LA), lime (MY);
  S6c                 VN hybrid split (UNSD explicit rows + n.e.s. by the APEC 2022 shares; VN_HYBRID_ELECTRICITY_ROWS.csv back-cast), same run.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from v4_common import CARS19, DEMAND_DIR, IND_V3, OUTC, REG_DIR, V4_DIR   # noqa: E402

CHEM = "chemical and petrochemical"
NMM = "non-metallic minerals"
PAPER = "paper pulp and print"
BL_GJ_T = 22.0                    # ETSAP chemical pulp black liquor (S2 / G3)
HVC_C1 = 3.2688016662080988       # JRC-IDEES 2019 energy use per t HVC, S2 convention (I1 HVC_VECTOR_CHECK.csv)
HVC_C2 = 5.190822737636671        # decision 210 item 5: consistent 2019 energy use (ETSAP SMR fuel part only)
HVC_EL_SHARE_C1 = 1.0 / 12.0      # ETSAP BAT olefins electricity share (S2 / G3), electricity per t unchanged under (c2)
HVC_VEC_B = {"electricity": 2.45374975383589, "heat": 0.18189882191578263, "gas": 3.29468660533621 - 1.47568072194036, "hydrogen": 0.17266107692307692}   # (b) 4.627
HVC_VEC_A = {"electricity": 2.45374975383589, "heat": 0.18189882191578263, "gas": 3.29468660533621, "hydrogen": 0.17266107692307692}                         # (a) 6.103 (sensitivity)
MEOH_GAS_PER_T = 4.777777778      # G1 Labuan energy-use intensity (PyPSA-Eur today 10.25 - ETSAP feedstock 5.47 MWh CH4/t)
MEOH_EL_PER_T = 0.167
METHANOL_DROP = ["BN", "ID", "MM", "PH", "SG", "TH", "VN"]   # every country with an s3_0 EU27-weight methanol load (I1 I1_3_METHANOL_LOAD_CHECK.csv)
RATIO_TO_OUT = {"elec": "electricity", "coal": "coal", "coke": "coal", "biomass": "biomass", "methane": "gas", "hydrogen": "hydrogen", "heat": "heat", "ammonia": "ammonia", "methanol": "methanol"}
APEC_COL = dict(coal="coal_pj", oil="oil_pj", gas="gas_pj", biomass="biomass_pj", electricity="electricity_pj")


def vz() -> dict:
    return {k: 0.0 for k in OUTC}


def vec(d: dict, scale: float = 1.0) -> dict:
    out = vz()
    for k, x in d.items():
        out[k] = out.get(k, 0.0) + float(x) * scale
    return out


def growth(cc: str, base_year: int) -> float:
    """S0 R2 / v3 product rule: G^((2050 - y_b) / 28 x 0.5), G = AEO8 D.2 real GDP 2050 / 2022 (INDUSTRY_OUTPUT_2050_M08B.csv)."""
    r = pd.read_csv(DEMAND_DIR / "INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country")
    return float(r.at[cc, "gdp_growth_2022_2050"]) ** ((2050 - base_year) / 28.0 * 0.5)


def rd(p: str) -> pd.DataFrame:
    return pd.read_csv(V4_DIR / p, keep_default_na=False, float_precision="round_trip")


# ---- pulp and paper ----------------------------------------------------------------------------------------------------------------------
def ratios():
    return pd.read_csv(REG_DIR / "INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0), pd.read_csv(REG_DIR / "INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv").set_index("sector")


def vec2050(sector: str, t: float) -> dict:
    r50, _ = ratios(); out = vz()
    for k, oc in RATIO_TO_OUT.items():
        out[oc] += float(r50.at[k, sector]) * t
    return out


def today_vec(sector: str, t: float) -> dict:
    r50, tday = ratios(); cars = ("elec", "coal", "coke", "methane", "biomass", "hydrogen", "heat")
    col = r50[sector]; tf = float(sum(col[c] for c in cars)); T = float(tday.at[sector, "today_total_mwh_per_t"])
    return {c: float(col[c]) / tf * T * t for c in cars}


def pp_item(cc: str, T: pd.DataFrame, part: str = "existing") -> dict | None:
    """Unified pulp and paper item (I2 i2_items.pp_item). part 'existing': items with 2019 output; 'new': lines with 2019 output 0 and a 2050 output."""
    T = T.copy(); q19, q50 = "q_2019_t", "q_2050_t"
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


# ---- HVC -------------------------------------------------------------------------------------------------------------------------------
def hvc_plants(basis: str = "b") -> dict:
    """basis b (main, decision 210 item 5): 2019 deduction HVC_C2 5.191, 2050 vector (b) 4.627 MWh/t; a (S2 basis, research.demand.v4.hvc_basis = a):
    3.269 / 6.103 MWh/t (= I2 i2_items.hvc_items basis "s2"); electricity per t 3.269 / 12 in both."""
    if basis not in ("a", "b"):
        raise ValueError(f"HVC basis {basis} not in (a, b)")
    out = {}
    for r in rd("HVC_PLANTS_V4.csv").to_dict("records"):
        d = dict(hvc19_t=float(r["hvc19_t"]), hvc50_base_t=float(r["hvc50_base_t"]), hvc50_new_t=float(r["hvc50_new_t"]), row=(r["row"] or None),
                 fuel_split=(json.loads(r["fuel_split"]) if r["fuel_split"] else None), src=r["source"])
        e_t = HVC_C2 if basis == "b" else HVC_C1
        el_t = HVC_C1 * HVC_EL_SHARE_C1
        d["el19_per_t"] = el_t; d["fuel19_per_t"] = e_t - el_t
        d["vec"] = HVC_VEC_B if basis == "b" else HVC_VEC_A
        out[r["country"]] = d
    return out


def hvc_item(h: dict, scale_u: float = 1.0) -> dict:
    return dict(name="hvc", row=h["row"], fuel_split=h["fuel_split"], fuel19=h["hvc19_t"] * h["fuel19_per_t"] * scale_u, el19=h["hvc19_t"] * h["el19_per_t"] * scale_u,
                v2050=vec(h["vec"], h["hvc50_base_t"] * scale_u))


# ---- methanol --------------------------------------------------------------------------------------------------------------------------
def derived(step: str | None = None) -> list:
    t = rd("PRODUCT_DERIVED_INPUTS_V4.csv")
    if step:
        t = t[t.step == step]
    return [dict(country=r["country"], name=r["name"], row=(r["row"] or None), fuel19=float(r["fuel19_mwh"]), el19=float(r["el19_mwh"]),
                 v2050={k: float(r[f"v2050_{k}_mwh"]) for k in OUTC}) for r in t.to_dict("records")]


def methanol_items() -> dict:
    out = {}
    my = [d for d in derived("S5f") if d["country"] == "MY"][0]
    out["MY"] = dict(name="methanol", row=None, fuel19=my["fuel19"], el19=my["el19"], fuel_split={"gas": 1.0}, v2050=vec(my["v2050"]))
    P = rd("METHANOL_PLANTS_V4.csv")
    for cc in ("ID", "BN"):
        r = P[(P.country == cc) & (P.status == "existing")].iloc[0]
        cap = float(r.capacity_kt) * 1000.0
        t19 = cap * float(r.utilisation); t50 = t19 * growth(cc, 2019)
        out[cc] = dict(name="methanol", row=(r.row or None), spill=bool(str(r.spill) == "True"), fuel19=t19 * MEOH_GAS_PER_T, el19=t19 * MEOH_EL_PER_T, fuel_split=None,
                       v2050=vec({"gas": MEOH_GAS_PER_T * t50, "electricity": MEOH_EL_PER_T * t50}))
    return out


def bn_neu_methanol_gas() -> dict:
    """BN: the 2019 plant energy use is in UNSD non-energy use (G4): the NEU gas falls by the same gas energy use, 2019 and 2050 (decision 210 item 7)."""
    P = rd("METHANOL_PLANTS_V4.csv"); r = P[(P.country == "BN") & (P.status == "existing")].iloc[0]
    t19 = float(r.capacity_kt) * 1000.0 * float(r.utilisation); t50 = t19 * growth("BN", 2019)
    return dict(country="BN", gas_2019_mwh=t19 * MEOH_GAS_PER_T, gas_2050_mwh=t50 * MEOH_GAS_PER_T, t_2019=t19, t_2050=t50)


# ---- VN hybrid split (S6c) -----------------------------------------------------------------------------------------------------------------
def vn_hybrid(cache: dict, el_rows: dict, bag_mwh: float = 0.0) -> dict:
    """G2 hybrid rule on the v4 cache: UNSD explicit rows kept; the n.e.s. amount of each carrier spread over the APEC 2022 rows that UNSD does not
    report for that carrier; electricity rows of iron and steel / chemicals back-cast from UNSD 2020 (I2 i2_chain.vn_hybrid)."""
    U = pd.DataFrame({r["carrier"]: {k: float(r[k]) for k in r if k not in ("country", "carrier")} for r in cache["records"] if r["country"] == "VN"})
    A = pd.read_csv(IND_V3 / "APEC2022_VN_INDUSTRY_PJ.csv").set_index("cache_subsector")
    A = A[[APEC_COL[c] for c in CARS19]].rename(columns={v: k for k, v in APEC_COL.items()}).reindex(U.index).fillna(0.0).astype(float)
    H = pd.DataFrame(0.0, index=U.index, columns=list(CARS19))
    for c in CARS19:
        explicit = [s for s in U.index if s != "other" and U.at[s, c] > 0]
        for s in explicit:
            H.at[s, c] = U.at[s, c]
        nes = U.at["other", c]
        if c == "biomass" and bag_mwh:
            H.at["food and tobacco", c] = bag_mwh; nes -= bag_mwh
            explicit = explicit + ["food and tobacco"]
        if c == "electricity":
            for s_, x in el_rows.items():
                H.at[s_, c] += x; nes -= x
            explicit = explicit + list(el_rows)
        w = A[c].copy(); w[explicit] = 0.0
        if w.sum() > 0:
            H[c] += nes * w / w.sum()
        else:
            H.at["other", c] += nes
    return {c: H[c].to_dict() for c in CARS19}


def set_vn_cache(cache: dict, H: dict) -> dict:
    c2 = copy.deepcopy(cache)
    for r in c2["records"]:
        if r["country"] == "VN":
            for s in r:
                if s not in ("country", "carrier"):
                    r[s] = repr(float(H[r["carrier"]].get(s, 0.0)))
    return c2


# ---- everything for v4_industry.build_steps ------------------------------------------------------------------------------------------------------------
def load_items(hvc_basis: str = "b") -> dict:
    import v3_industry as v3
    it = {}
    cap = rd("CAPTIVE_COAL_2019.csv")
    mv = []
    for r in cap.to_dict("records"):
        if not r["coal_row"] or float(r["coal_kt"]) <= 0:
            continue
        mv.append((r["country"], r["coal_row"], "coal", float(r["coal_kt"]) * float(r["gj_per_t"]) / 3.6 * 1e3))
        if r["electricity_row"]:
            e = float(r["e_mwh"]) if r["e_mwh"] != "" else float(r["e_gwh"]) * 1e3
            mv.append((r["country"], r["electricity_row"], "electricity", -e))
    it["captive"] = mv
    cem = rd("CEMENT_USGS_2019.csv")
    it["cement_usgs_2019_t"] = {r["country"]: float(r["cement_2019_t"]) for r in cem.to_dict("records")}
    it["edgar_zero"] = [r["country"] for r in cem.to_dict("records") if str(r["edgar_2a1_zero"]) == "True"]
    fut = v3.future_vectors(); ne = v3.nickel_unit_energy()
    it["nickel_2023"] = v3.nonferrous(fut, "nf2023", ne)[0]["ID"]["nonferrous_nickel"]
    F = rd("PULP_PAPER_FAOSTAT_V4.csv")
    order = list(dict.fromkeys(F.country))
    it["pp"] = {cc: x for cc in order if (x := pp_item(cc, F[F.country == cc]))}
    it["pp_new"] = {cc: x for cc in order if (x := pp_item(cc, F[F.country == cc], "new"))}
    H = hvc_plants(hvc_basis)   # V4 D1: research.demand.v4.hvc_basis
    it["hvc_plants"] = H
    it["hvc"] = {cc: hvc_item(h) for cc, h in H.items() if h["hvc19_t"] > 0 or h["hvc50_base_t"] > 0}
    it["methanol"] = methanol_items(); it["methanol_drop"] = list(METHANOL_DROP)
    new = {}
    for cc, h in H.items():
        if h["hvc50_new_t"] > 0:
            new.setdefault(cc, {})["hvc_new_plants"] = vec(h["vec"], h["hvc50_new_t"])
    myn = [d for d in derived("S5g") if d["country"] == "MY" and d["name"] == "methanol_new_plants"][0]
    new.setdefault("MY", {})["methanol_new_plants"] = vec(myn["v2050"])
    for cc, x in it["pp_new"].items():
        new.setdefault(cc, {})["pulp_paper_new_lines"] = x["v2050"]
    it["new_plants"] = new
    it["my_ammonia_dup"] = [(r["country"], r["sub"], r["carrier"], float(r["mwh_2019"])) for r in rd("MY_AMMONIA_FUEL_DUPLICATE.csv").to_dict("records")]
    for grp in ("glass", "alumina", "copper", "lime"):
        it[grp] = {d["country"]: dict(name=d["name"], row=d["row"], fuel19=d["fuel19"], el19=d["el19"], v2050=vec(d["v2050"])) for d in derived("S6b") if d["name"] == grp}
    it["vn_el_rows"] = {r["sub"]: float(r["mwh_2019"]) for r in rd("VN_HYBRID_ELECTRICITY_ROWS.csv").to_dict("records")}
    it["bn_neu_methanol"] = bn_neu_methanol_gas()
    return it


def main():
    it = load_items()
    rows = []
    for step, grp in (("S5d", "pp"), ("S5e", "hvc"), ("S5f", "methanol"), ("S6b", "glass"), ("S6b", "alumina"), ("S6b", "copper"), ("S6b", "lime")):
        for cc, x in it[grp].items():
            rows.append(dict(step=step, country=cc, name=x["name"], row=x.get("row") or "other", fuel19_mwh=x["fuel19"], el19_mwh=x["el19"], spill=x.get("spill", True),
                             v2050_total_mwh=sum(x["v2050"].values()), **{f"v2050_{k}_mwh": x["v2050"][k] for k in OUTC},
                             closed_loop_bl19_mwh=x.get("closed_loop_bl19", ""), closed_loop_bl50_mwh=x.get("closed_loop_bl50", "")))
    for cc, d in it["new_plants"].items():
        for k, v in d.items():
            rows.append(dict(step="S5g", country=cc, name=k, row="", fuel19_mwh=0.0, el19_mwh=0.0, spill="", v2050_total_mwh=sum(v.values()), **{f"v2050_{kk}_mwh": v[kk] for kk in OUTC}))
    pd.DataFrame(rows).to_csv(V4_DIR / "PRODUCT_ITEMS_V4.csv", index=False, float_format="%.9g", lineterminator="\n")
    print(pd.DataFrame(rows)[["step", "country", "name", "fuel19_mwh", "el19_mwh", "v2050_total_mwh"]].to_string())


if __name__ == "__main__":
    main()
