"""G2-2: captive power of Viet Nam (B-G2 item 3; A3 item 6 = decision 204 items 1-2; S1 method, S2 section 5 screen).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/v4w07g2_captive.py

1. UNSD 2019 autoproducer rows (SDMX = export for these rows): fuels in transformation, combustible output, capacity; the inequality of S2.
2. GEM GIPT 2026-09 coal units of VN: 'Captive Industry Type' units operating at the end of 2019 (S1 rule), plus a name / owner check of the
   untyped operating units.
3. S1 estimate C = average MW x hours x t/MWh (tonnes first, energy only at the end, W11 4.3): hours and t/MWh with sources from the UNSD
   SDMX series of VN (no number from memory). Low / mid: the UNSD autoproducer coal already in transformation (2,578.6 kt) is deducted; high: not.
4. Reverse check (S2 note: implied efficiency 0.12): fuel in autoproducer transformation that the reported output cannot explain.
Writes tables/VN_CAPTIVE_UNITS_GIPT.csv, tables/VN_CAPTIVE_ESTIMATE.csv, tables/VN_AUTOPRODUCER_2019.csv, evidence/_captive_evidence.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4w07g2_common as cm   # noqa: E402

T = cm.WORK / "tables"
GIPT = cm.REPO / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv"
TYPE_TO_SUB = {"iron & steel": "iron and steel", "pulp & paper": "paper pulp and print", "agriculture": "food and tobacco", "chemicals": "chemical and petrochemical"}
YEARS = range(2015, 2023)


def main():
    ev = cm.Ev("captive")
    s = cm.sdmx_long()
    v = lambda com, tr, y=2019: float(s[(s.commodity == com) & (s.transaction == tr) & (s.year == y)].value.sum())
    st = lambda com, tr, y=2019: ";".join(s[(s.commodity == com) & (s.transaction == tr) & (s.year == y)].obs_status.astype(str))
    ff = cm.frozen_factors()
    # ---------------- 1. UNSD autoproducer 2019 ----------------
    ap = [dict(item="hard coal, transformation in electricity plants - autoproducers", unit="kt", q=v("0100", "08812"), status=st("0100", "08812"),
               twh_v3=v("0100", "08812") * ff["Hard coal"], twh_unsd_ncv=v("0100", "08812") * 23.446 / 3600),
          dict(item="natural gas, autoproducers", unit="TJ GCV", q=v("3000", "08812"), status=st("3000", "08812"), twh_v3=v("3000", "08812") * 0.9 / 3600,
               twh_unsd_ncv=v("3000", "08812") * 0.9 / 3600),
          dict(item="fuel oil, autoproducers", unit="kt", q=v("4680", "08812"), status=st("4680", "08812"), twh_v3=v("4680", "08812") * ff["Fuel oil"],
               twh_unsd_ncv=v("4680", "08812") * 40.4 / 3600),
          dict(item="fuelwood, autoproducers", unit="thousand m3", q=v("5110", "08812"), status=st("5110", "08812"), twh_v3=v("5110", "08812") * ff["Fuelwood"],
               twh_unsd_ncv=v("5110", "08812") * 9.135 / 3600),
          dict(item="electricity from combustible fuels - autoproducer", unit="GWh", q=v("7000", "016C"), status=st("7000", "016C"), twh_v3=np.nan, twh_unsd_ncv=np.nan),
          dict(item="net installed capacity, combustible fuels - autoproducers", unit="MW", q=v("EC", "13342"), status=st("EC", "13342"), twh_v3=np.nan, twh_unsd_ncv=np.nan),
          dict(item="thermal electricity from solid biofuels (main + auto)", unit="GWh", q=v("7000T", "01SBF"), status=st("7000T", "01SBF"), twh_v3=np.nan, twh_unsd_ncv=np.nan)]
    AP = pd.DataFrame(ap); AP.to_csv(T / "VN_AUTOPRODUCER_2019.csv", index=False, float_format="%.6f")
    fuel_twh = float(AP.twh_v3.iloc[:4].sum()); out_gwh = float(AP.q.iloc[4]); cap_mw = float(AP.q.iloc[5])
    for r in AP.itertuples():
        ev.put(f"ap2019.{r.Index}.{r.item.split(',')[0].replace(' ', '_')}", r.q, r.unit, f"UNSD SDMX 2019: {r.item} (status {r.status})", "VERIFIED", "B" if "E" in r.status else "A")
    ev.put("ap2019_fuel_twh_v3", fuel_twh, "TWh", "sum of the four autoproducer fuels x frozen upstream factors (gas x0.9)", "EXACT", "B")
    ev.put("ap2019_implied_efficiency", out_gwh / 1e3 / fuel_twh, "ratio", "autoproducer combustible output / fuel in transformation", "EXACT", "B")
    ev.put("ap2019_hours_combustible", out_gwh / cap_mw * 1e3, "h", "UNSD 2019 autoproducer combustible output / combustible capacity (both E)", "EXACT", "B")
    # ---------------- power-sector coal series (sources of hours and t/MWh) ----------------
    gi = pd.read_csv(GIPT, low_memory=False)
    vn = gi[(gi.iso == "VN") & gi.Type.eq("coal")].copy()
    vn["sy"] = pd.to_numeric(vn["Start year"], errors="coerce"); vn["ry"] = pd.to_numeric(vn["Retired year"], errors="coerce")
    was = vn.Status.isin(["operating", "retired", "mothballed"])
    ser = []
    for y in YEARS:
        op = was & (vn.sy <= y) & ~(vn.ry <= y)
        w = np.where(op, np.where(vn.sy == y, 0.5, 1.0), 0.0)
        mw_avg = float((vn["Capacity (MW)"] * w).sum())
        coal_kt = v("0100", "088", y); gen = v("7000T", "01CL", y)
        ser.append(dict(year=y, coal_to_power_kt=coal_kt, coal_status=st("0100", "088", y), coal_gen_gwh=gen, gen_status=st("7000T", "01CL", y),
                        t_per_mwh=coal_kt / gen if gen else np.nan, gipt_coal_mw_avg=mw_avg, hours_fleet=gen / mw_avg * 1e3 if mw_avg else np.nan,
                        cf_hard_coal=float(s[(s.commodity == "0100") & (s.transaction == "088") & (s.year == y)].conversion_factor.iloc[0])))
    SER = pd.DataFrame(ser); SER.to_csv(T / "VN_COAL_POWER_SERIES.csv", index=False, float_format="%.6f")
    r19 = SER.set_index("year").loc[2019]
    # ---------------- 2. GIPT captive units ----------------
    vn["op_2019_yearend"] = was & (vn.sy <= 2019) & ~(vn.ry <= 2019)
    vn["w_2019_avg"] = np.where(vn.op_2019_yearend, np.where(vn.sy == 2019, 0.5, 1.0), 0.0)
    capt = vn[vn["Captive Industry Type"].notna()].copy()
    capt["v4_subsector"] = capt["Captive Industry Type"].map(TYPE_TO_SUB)
    capt["note"] = np.where(capt["Plant / Project name"].str.contains("Nhon Trach Formosa"),
                            "GIPT type iron & steel; owner Hung Nghiep Formosa (Formosa Industries, Nhon Trach): fibre / textile / chemical complex, no steel plant known at the site (INFERENCE)",
                            np.where(capt["Plant / Project name"].str.contains("Vedan"), "Vedan: monosodium glutamate / food plant (GIPT type agriculture -> food and tobacco, INFERENCE)", ""))
    keep = ["GEM unit/phase ID", "Plant / Project name", "Unit / Phase name", "Capacity (MW)", "Status", "Start year", "Retired year", "Captive Industry Type",
            "Captive Industry Use", "Owner(s)", "Parent(s)", "Technology", "CHP", "Latitude", "Longitude", "Subnational unit (state, province)", "op_2019_yearend",
            "w_2019_avg", "v4_subsector", "note"]
    capt[keep].sort_values(["op_2019_yearend", "Plant / Project name", "Unit / Phase name"], ascending=[False, True, True]).to_csv(T / "VN_CAPTIVE_UNITS_GIPT.csv", index=False)
    c19 = capt[capt.op_2019_yearend]
    mw_end = float(c19["Capacity (MW)"].sum()); mw_avg = float((c19["Capacity (MW)"] * c19.w_2019_avg).sum())
    ev.put("gipt_captive_coal_mw_2019_yearend", mw_end, "MW", "GEM GIPT 2026-09, VN coal units with 'Captive Industry Type', operating at the end of 2019", "VERIFIED", "B")
    ev.put("gipt_captive_coal_mw_2019_avg", mw_avg, "MW", "same, units starting in 2019 counted half", "EXACT", "B")
    for t, z in c19.groupby("Captive Industry Type"):
        ev.put(f"gipt_captive_mw_2019.{t}", float(z["Capacity (MW)"].sum()), "MW", "GIPT 'Captive Industry Type'", "VERIFIED", "B")
    # untyped operating units whose name / owner looks industrial (S1 check)
    rest = vn[vn["Captive Industry Type"].isna() & vn.op_2019_yearend].copy()
    pat = r"Formosa|Hoa Phat|steel|Steel|cement|Cement|paper|Paper|sugar|Sugar|Vinachem|fertili|Fertili|chemical|Chemical|textile|Textile|Vedan|Lee & Man"
    sus = rest[(rest["Plant / Project name"].fillna("") + " " + rest["Owner(s)"].fillna("")).str.contains(pat, regex=True)]
    sus[["Plant / Project name", "Unit / Phase name", "Capacity (MW)", "Start year", "Owner(s)", "Technology", "CHP"]].to_csv(T / "VN_GIPT_UNTYPED_INDUSTRIAL_NAMES.csv", index=False)
    ev.put("gipt_untyped_industrial_names_2019_mw", float(sus["Capacity (MW)"].sum()), "MW", "operating 2019 units without captive type whose name/owner matches an industrial pattern", "VERIFIED", "B")
    # ---------------- 3. S1 estimate (tonnes first) ----------------
    s1519 = SER[(SER.year >= 2015) & (SER.year <= 2022)]
    # mid = median 2015-2022: the 2019 ratio is an outlier (coal electricity printed as the round 100,000 GWh while 2020 generated 119,147 GWh
    # from the same 59.3 Mt), so the 2019 value is used as the high end only
    hours = dict(low=(out_gwh / cap_mw * 1e3, "UNSD 2019 autoproducer combustible output 4,200 GWh / combustible capacity 5,125 MW (both E)"),
                 mid=(float(s1519.hours_fleet.median()), "median 2015-2022 of UNSD coal electricity (main + auto) / GIPT VN coal capacity (year average)"),
                 high=(float(s1519.hours_fleet.max()), f"maximum 2015-2022 of the same ratio (year {int(s1519.loc[s1519.hours_fleet.idxmax(), 'year'])})"))
    tpm = dict(low=(float(s1519.t_per_mwh.min()), f"UNSD coal to power / coal electricity, minimum 2015-2022 (year {int(s1519.loc[s1519.t_per_mwh.idxmin(), 'year'])})"),
               mid=(float(s1519.t_per_mwh.median()), "median 2015-2022 of UNSD coal to electricity plants / coal electricity"),
               high=(float(s1519.t_per_mwh.max()), f"maximum 2015-2022 (year {int(s1519.loc[s1519.t_per_mwh.idxmax(), 'year'])}: 59,141 kt / 100,000 GWh)"))
    ap_coal_kt = float(AP.q.iloc[0])
    est = []
    for lv in ("low", "mid", "high"):
        mw = mw_end if lv == "high" else mw_avg
        gen = mw * hours[lv][0] / 1e3   # GWh
        c_kt = gen * tpm[lv][0]   # GWh x t/MWh = kt
        ded = 0.0 if lv == "high" else ap_coal_kt
        ind_kt = max(0.0, c_kt - ded)
        e_gwh = gen * (ind_kt / c_kt) if c_kt else 0.0
        est.append(dict(level=lv, capacity_mw=mw, hours=hours[lv][0], hours_source=hours[lv][1], t_per_mwh=tpm[lv][0], t_per_mwh_source=tpm[lv][1],
                        generation_gwh=gen, coal_total_kt=c_kt, unsd_autoproducer_coal_kt_deducted=ded, coal_in_industry_kt=ind_kt,
                        C_twh_v3=ind_kt * ff["Hard coal"], C_twh_unsd_ncv=ind_kt * 23.446 / 3600, E_twh=e_gwh / 1e3,
                        coal_total_vs_unsd_autoproducer=c_kt / ap_coal_kt))
    EST = pd.DataFrame(est); EST.to_csv(T / "VN_CAPTIVE_ESTIMATE.csv", index=False, float_format="%.6f")
    for r in EST.itertuples():
        for k in ("hours", "t_per_mwh", "generation_gwh", "coal_total_kt", "coal_in_industry_kt", "C_twh_v3", "C_twh_unsd_ncv", "E_twh"):
            ev.put(f"est.{r.level}.{k}", float(getattr(r, k)), {"hours": "h", "t_per_mwh": "t/MWh", "generation_gwh": "GWh", "coal_total_kt": "kt", "coal_in_industry_kt": "kt"}.get(k, "TWh"),
                   f"S1 method: {r.hours_source}; {r.t_per_mwh_source}", "INFERENCE", "C")
    # ---------------- 4. reverse check ----------------
    eff_coal = 1.0 / (float(r19.t_per_mwh) * 23.446 / 3.6)   # implied UNSD coal-power efficiency at the UNSD NCV
    need_coal = ap_coal_kt / float(r19.t_per_mwh)   # GWh the autoproducer coal can generate at the UNSD fleet rate
    ev.put("reverse.ap_coal_can_generate_gwh", need_coal, "GWh", "UNSD autoproducer coal 2,578.6 kt / UNSD 2019 fleet 0.5914 t/MWh", "EXACT", "B")
    ev.put("reverse.ap_fuelwood_twh", float(AP.twh_v3.iloc[3]), "TWh", "UNSD 2019 fuelwood to autoproducers (4,100 thousand m3)", "EXACT", "B")
    ev.put("reverse.solid_biofuel_electricity_gwh", float(AP.q.iloc[6]), "GWh", "UNSD 2019 thermal electricity from solid biofuels, all producers", "VERIFIED", "A")
    ev.put("reverse.coal_fleet_efficiency_at_unsd_ncv", eff_coal, "ratio", "100,000 GWh / (59,141 kt x 23.446 GJ/t)", "EXACT", "B")
    ev.extra = dict(power_series=SER.to_dict("records"), estimate=EST.to_dict("records"))
    ev.write(cm.WORK / "evidence/_captive_evidence.json")
    pd.set_option("display.width", 250)
    print(AP.to_string()); print(SER.round(4).to_string()); print(EST.round(3).to_string())
    print(c19[["Plant / Project name", "Unit / Phase name", "Capacity (MW)", "Start year", "Captive Industry Type", "Technology", "CHP"]].to_string())
    print(sus[["Plant / Project name", "Unit / Phase name", "Capacity (MW)", "Start year", "Owner(s)"]].to_string())
    print("ap coal can generate GWh", round(need_coal), "fleet eff", round(eff_coal, 4))


if __name__ == "__main__":
    main()
