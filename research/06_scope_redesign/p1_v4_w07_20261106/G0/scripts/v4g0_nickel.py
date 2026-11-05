"""V4 W07 G0 item 2: nickel unit energy from the original Wei et al. 2020 (Energies 13(21) 5664, downloads/17_nickel_literature/), by product.

    PYTHONHASHSEED=0 python scripts/v4g0_nickel.py          (WSL pypsa-earth python; read only)

Table 8 (PDF p.10) inventory per tonne of alloy and Table 3 (PDF p.6) heating values, read from the page text (G0/extracted/wei2020, made by
v4g0_wei_text.py; values asserted against the text here). Same accounting as v3 (v3_industry.nickel_unit_energy): final energy per t contained Ni
= electricity + fuel (drying, kiln / sinter, reductant), mining and auxiliary materials (compressed air, oxygen, lime, electrodes) excluded;
fuel -> useful heat > 400 C x 0.90.
Rule of the instruction: NPI production -> Case 4-NPI, ferronickel -> Case 3-FeNi (Case 3 for all products = v3 / S2, as comparison). Matte has no
Wei case: kept on Case 3 (v3). Cross-checks against 2019 statistics: electricity implied vs GIPT nickel captive generation (S1), coke implied vs
UNSD 2019 industry coke, and the process route named for Indonesian NPI in CREA/GEM 2025 (S1 extracted text).
Outputs ID_NICKEL_WEI2020_INVENTORY.csv, ID_NICKEL_UNIT_ENERGY.csv, ID_NICKEL_CHECKS.csv, evidence/_nickel_evidence.json.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4g0_common as cm   # noqa: E402

TXT = cm.WORK / "extracted/wei2020"
PDF = cm.S2WORK / "downloads/17_nickel_literature/energies-13-05664 (1).pdf"
PDF_SHA = "8695d6c485b6c9e17d3cb575c636250e8925035c9aa82aa80ff9e5e106640d36"
LHV = {"natural gas": 50.0, "coal": 27.5, "anthracite": 29.0, "coke": 28.5, "diesel": 43.3}   # Wei 2020 Table 3 (PDF p.6), MJ/kg
# Table 8 (PDF p.10), per t alloy: (case, product, ni_fraction, step, item, quantity, unit, fuel key, counted_as)
INV = [("Case 3-FeNi", "ferronickel", 0.35, "mining", "diesel", 76, "kg", "diesel", "excluded"),
       ("Case 3-FeNi", "ferronickel", 0.35, "mining", "electricity", 391, "kWh", None, "excluded"),
       ("Case 3-FeNi", "ferronickel", 0.35, "drying", "natural gas", 308, "kg", "natural gas", "fuel"),
       ("Case 3-FeNi", "ferronickel", 0.35, "calcination", "natural gas", 308, "kg", "natural gas", "fuel"),
       ("Case 3-FeNi", "ferronickel", 0.35, "calcination", "anthracite reductant", 569, "kg", "anthracite", "fuel"),
       ("Case 3-FeNi", "ferronickel", 0.35, "smelting", "electricity", 7237, "kWh", None, "electricity"),
       ("Case 3-FeNi", "ferronickel", 0.35, "smelting", "electrode", 19, "kg", None, "excluded (auxiliary material)"),
       ("Case 3-FeNi", "ferronickel", 0.35, "refining", "electricity", 1081, "kWh", None, "electricity"),
       ("Case 4-NPI", "nickel pig iron", 0.10, "mining", "diesel", 29, "kg", "diesel", "excluded"),
       ("Case 4-NPI", "nickel pig iron", 0.10, "mining", "electricity", 146, "kWh", None, "excluded"),
       ("Case 4-NPI", "nickel pig iron", 0.10, "sintering", "coal", 603, "kg", "coal", "fuel"),
       ("Case 4-NPI", "nickel pig iron", 0.10, "sintering", "electricity", 104, "kWh", None, "electricity"),
       ("Case 4-NPI", "nickel pig iron", 0.10, "sintering", "compressed air", 3748, "Nm3", None, "excluded (auxiliary)"),
       ("Case 4-NPI", "nickel pig iron", 0.10, "sintering", "lime", 27, "kg", None, "excluded (material)"),
       ("Case 4-NPI", "nickel pig iron", 0.10, "smelting (blast furnace)", "coke (fuel + reductant)", 1239, "kg", "coke", "fuel"),
       ("Case 4-NPI", "nickel pig iron", 0.10, "smelting (blast furnace)", "oxygen", 182, "Nm3", None, "excluded (auxiliary material)"),
       ("Case 4-NPI", "nickel pig iron", 0.10, "smelting (blast furnace)", "lime flux", 335, "kg", None, "excluded (material)")]
NPI_GROSS_2019_T = 3_200_000.0   # USGS MYB 2023 Indonesia table 1 (v3_industry.NI_NPI_NI_FRACTION = 380,000 / 3,200,000)
UNSD_COKE_INDUSTRY_2019_KT = {"iron and steel": 520.3, "other (n.e.s.)": 57.8}   # UNdata 2019 (W11 NCV_CACHE_RATIOS_2019.csv commodities)
HEESI_METALLURGY_COAL_2019_KT = 10064.75   # HEESI 2025 table 6.1.4 (S1 ID_CAPTIVE_CROSSCHECK.csv reference)


def check_text():
    t10 = (TXT / "p10.txt").read_text(encoding="utf-8"); t6 = (TXT / "p06_plain.txt").read_text(encoding="utf-8"); t7 = (TXT / "p07_plain.txt").read_text(encoding="utf-8")
    flat = re.sub(r"\s+", " ", t10)
    need10 = ["Case 3-FeNi Case 4-NPI", "Natural Gas: 308", "Coal: 603", "Anthracite: 569", "104 b", "7237f", "Coke: 1239", "Electricity: 1081 kWh",
              "391 146", "76 29", "Lime: 27", "Lime: 335", "137 4619", "182"]
    miss = [s for s in need10 if s not in flat]
    need6 = ["Natural Gas 50 MJ /kg", "Coal 27.5 MJ /kg", "Anthracite 29 MJ /kg", "Coke 28.5 MJ /kg", "Diesel (stationary combustion) 43.3 MJ /kg"]
    miss += [s for s in need6 if s not in t6]
    need7 = ["3 Colombia Open-pit Laterite (2.20) FeNi (35) RKEF", "4 Indonesia Open-pit Laterite (1.88) NPI (10) Blast"]
    miss += [s for s in need7 if s not in t7]
    if miss:
        raise SystemExit(f"Wei 2020 text check failed: {miss}")
    return len(need10) + len(need6) + len(need7)


def unit_energy(case: str) -> dict:
    rows = [r for r in INV if r[0] == case]
    ni = rows[0][2]
    el = sum(r[5] for r in rows if r[8] == "electricity") / 1000.0 / ni
    fu = sum(r[5] * LHV[r[7]] for r in rows if r[8] == "fuel") / 3600.0 / ni
    return dict(case=case, ni_fraction=ni, electricity_mwh_per_t_ni=el, fuel_mwh_per_t_ni=fu, useful_heat_mwh_per_t_ni=fu * 0.90)


def vectors(mode: str = "by_product", base: str = "2023") -> dict:
    """{product: {carrier: MWh 2050}} and the totals; mode 'by_product' (instruction: NPI Case 4, FeNi / matte Case 3) or 'case3' (v3 / S2)."""
    v3 = cm.import_v3()
    p = pd.read_csv(cm.REPO / "research_inputs/industry_v3/NONFERROUS_PRODUCTION_V3.csv")
    p = p[(p.country == "ID") & (p.route == "nickel")].set_index("commodity")
    g = cm.growth(int(base))
    c3, c4 = unit_energy("Case 3-FeNi"), unit_energy("Case 4-NPI")
    ne = v3.nickel_unit_energy()
    if abs(ne["electricity_mwh_per_t_ni"] - c3["electricity_mwh_per_t_ni"]) > 1e-9 or abs(ne["fuel_mwh_per_t_ni"] - c3["fuel_mwh_per_t_ni"]) > 1e-9:
        raise SystemExit(f"Case 3 from the original text differs from the repository table NICKEL_ENERGY_WEI2020.csv: {ne} vs {c3}")
    out, tot = {}, {k: 0.0 for k in cm.OUTC}
    for com in p.index:
        ue = c4 if (mode == "by_product" and com == "nickel_npi_ni_content") else c3
        q = float(p.at[com, f"q_{base}_t"]) * g
        v = {k: 0.0 for k in cm.OUTC}
        v["electricity"] = q * ue["electricity_mwh_per_t_ni"]; v["heat_high"] = q * ue["useful_heat_mwh_per_t_ni"]
        out[com] = dict(case=ue["case"], q_base_t=float(p.at[com, f"q_{base}_t"]), q_2050_t=q, vec=v)
        for k in cm.OUTC:
            tot[k] += v[k]
    return dict(products=out, total=tot, growth=g)


def main():
    ev = cm.Ev("ni")
    if cm.sha256(PDF) != PDF_SHA:
        raise SystemExit("Wei 2020 PDF SHA256 changed")
    n_ok = check_text()
    ev.put("wei2020.pdf_sha256_checked", 1, "-", f"{PDF.name} SHA256 {PDF_SHA[:16]}..., 22 pages; {n_ok} text strings of Tables 3, 4, 8 asserted", "VERIFIED", "B")
    I = pd.DataFrame([dict(case=r[0], product=r[1], ni_fraction=r[2], step=r[3], item=r[4], quantity_per_t_alloy=r[5], unit=r[6],
                           lhv_mj_per_kg=(LHV[r[7]] if r[7] else None), counted_as=r[8],
                           source="Wei et al. 2020 Energies 13(21) 5664, Table 8 (PDF p.10); LHV Table 3 (PDF p.6)") for r in INV])
    I.to_csv(cm.WORK / "ID_NICKEL_WEI2020_INVENTORY.csv", index=False)
    c3, c4 = unit_energy("Case 3-FeNi"), unit_energy("Case 4-NPI")
    for c in (c3, c4):
        for k in ("electricity_mwh_per_t_ni", "fuel_mwh_per_t_ni", "useful_heat_mwh_per_t_ni"):
            ev.put(f"unit.{c['case']}.{k}", c[k], "MWh/t Ni", "Wei 2020 Table 8 / Table 3, mining and auxiliary materials excluded (v3 accounting)", "EXACT", "C")
    # oxygen of Case 4 (excluded as an auxiliary material, as v3 does for Case 3): electricity if produced on site, Wei Table 3 primary 18.2 MJ/kg at PEF 0.34
    o2_el = 182 * 1.429 * 18.2 * 0.34 / 3600.0 / 0.10   # MWh/t Ni, INFERENCE (density 1.429 kg/Nm3)
    ev.put("unit.Case 4-NPI.oxygen_electricity_if_counted", o2_el, "MWh/t Ni", "182 Nm3 x 1.429 kg/Nm3 x 18.2 MJ/kg primary x PEF 0.34 (Wei Table 3) / 0.10; not counted (v3 accounting)", "INFERENCE", "C")
    V = {m: vectors(m) for m in ("by_product", "case3")}
    V19 = {m: vectors(m, "2019") for m in ("by_product", "case3")}
    v3 = cm.import_v3()
    nf23 = v3.nonferrous(v3.future_vectors(), "nf2023", v3.nickel_unit_energy())[0]["ID"]["nonferrous_nickel"]
    dev = max(abs(V["case3"]["total"][k] - nf23.get(k, 0.0)) for k in cm.OUTC)
    if dev > 1e-3:
        raise SystemExit(f"Case 3 2023-base vector differs from v3_industry nf2023 by {dev} MWh")
    ev.put("vector.case3_2023_vs_v3_nf2023_max_abs_dev", dev, "MWh", "v3_industry.nonferrous(nf2023) ID nickel", "EXACT", "-")
    U = []
    for m in ("by_product", "case3"):
        for com, x in V[m]["products"].items():
            u = c4 if x["case"] == "Case 4-NPI" else c3
            U.append(dict(mode=m, product=com, wei_case=x["case"], electricity_mwh_per_t_ni=u["electricity_mwh_per_t_ni"], fuel_mwh_per_t_ni=u["fuel_mwh_per_t_ni"],
                          useful_heat_gt400_mwh_per_t_ni=u["useful_heat_mwh_per_t_ni"], q_2019_t_ni=V19[m]["products"][com]["q_base_t"], q_2023_t_ni=x["q_base_t"],
                          growth_2023_2050=V[m]["growth"], q_2050_t_ni=x["q_2050_t"], electricity_2050_twh=x["vec"]["electricity"] / 1e6,
                          heat_gt400_2050_twh=x["vec"]["heat_high"] / 1e6, total_2050_twh=(x["vec"]["electricity"] + x["vec"]["heat_high"]) / 1e6,
                          electricity_2019_twh=V19[m]["products"][com]["q_base_t"] * u["electricity_mwh_per_t_ni"] / 1e6,
                          fuel_2019_twh=V19[m]["products"][com]["q_base_t"] * u["fuel_mwh_per_t_ni"] / 1e6))
    U = pd.DataFrame(U); U.to_csv(cm.WORK / "ID_NICKEL_UNIT_ENERGY.csv", index=False, float_format="%.6f")
    for m in ("by_product", "case3"):
        t = V[m]["total"]
        ev.put(f"2050.{m}.total", (t["electricity"] + t["heat_high"]) / 1e6, "TWh", "USGS 2023 Ni content x G^((2050-2023)/28 x 0.5) x unit energy", "EXACT", "C")
        ev.put(f"2050.{m}.electricity", t["electricity"] / 1e6, "TWh", "same", "EXACT", "C")
        ev.put(f"2050.{m}.heat_gt400", t["heat_high"] / 1e6, "TWh", "same", "EXACT", "C")
    # ---- cross-checks against 2019 statistics
    cap = pd.read_csv(cm.S2D / "s1/ID_CAPTIVE_COAL_2019.csv"); capn = cap[(cap.v3_subsector == "nickel")].set_index("level").gen_gwh.astype(float)   # as S1 cross-check
    q19 = {com: x["q_base_t"] for com, x in V19["by_product"]["products"].items()}
    el19 = {m: sum(r.electricity_2019_twh for r in U[U["mode"] == m].itertuples()) for m in ("by_product", "case3")}
    coke_case4_t_per_t_ni = 1239 / 1000 / 0.10
    coal_case4_t_per_t_ni = 603 / 1000 / 0.10
    coke_unsd = sum(UNSD_COKE_INDUSTRY_2019_KT.values())
    C = []
    for lv in ("low", "central", "mid", "high"):
        g_ = float(capn.at[lv]) / 1e3
        C.append(dict(check="2019 nickel electricity implied by the unit energy vs GIPT nickel captive coal generation (S1)", level=lv, mode="by_product (NPI Case 4)",
                      implied=el19["by_product"], reference=g_, unit="TWh", ratio=el19["by_product"] / g_,
                      note="Case 4 is a blast-furnace route (sinter 104 kWh/t NPI); the captive coal plants for nickel (2,037 MW 2019 average) imply electric smelting"))
        C.append(dict(check="2019 nickel electricity implied by the unit energy vs GIPT nickel captive coal generation (S1)", level=lv, mode="case3 (v3 / S2)",
                      implied=el19["case3"], reference=g_, unit="TWh", ratio=el19["case3"] / g_, note="S1 section 1.6: mid level 0.92"))
    C.append(dict(check="2019 coke implied by Case 4 for NPI (12.39 t coke per t Ni) vs UNSD 2019 ID industry coke-oven coke consumption", level="", mode="by_product (NPI Case 4)",
                  implied=q19["nickel_npi_ni_content"] * coke_case4_t_per_t_ni / 1e3, reference=coke_unsd, unit="kt", ratio=q19["nickel_npi_ni_content"] * coke_case4_t_per_t_ni / 1e3 / coke_unsd,
                  note=f"per t gross NPI (USGS 3.2 Mt) {NPI_GROSS_2019_T * 1.239 / 1e6:.2f} Mt; UNSD: iron and steel 520.3 + n.e.s. 57.8 kt"))
    C.append(dict(check="2019 coal implied by Case 4 sintering for NPI (6.03 t per t Ni) + nickel captive coal (S1 mid) vs HEESI 2019 iron, steel and metallurgy coal sales", level="mid",
                  mode="by_product (NPI Case 4)", implied=q19["nickel_npi_ni_content"] * coal_case4_t_per_t_ni / 1e3 + float(cap[(cap.v3_subsector == "nickel") & (cap.level == "mid")].coal_kt.iloc[0]),
                  reference=HEESI_METALLURGY_COAL_2019_KT, unit="kt", ratio=None, note="coke excluded (coke is a separate commodity)"))
    C.append(dict(check="process route of Indonesian NPI named on disk", level="", mode="-", implied=None, reference=None, unit="-", ratio=None,
                  note="CREA/GEM 2025 (S1 extracted text p.11): captive boilers supply 'high-baseload electricity required for Rotary Kiln Electric Furnace (RKEF) lines'; 'PT Angel Nickel Industry, which operates RKEF lines to produce NPI'. Wei Table 4: Case 4 NPI = blast furnace smelting, Case 3 FeNi = RKEF (Colombia)"))
    CH = pd.DataFrame(C); CH["ratio"] = pd.to_numeric(CH.ratio)
    CH.loc[CH.check.str.contains("coal implied"), "ratio"] = CH.loc[CH.check.str.contains("coal implied"), "implied"] / HEESI_METALLURGY_COAL_2019_KT
    CH.to_csv(cm.WORK / "ID_NICKEL_CHECKS.csv", index=False, float_format="%.6f")
    for r in CH.itertuples():
        if pd.notna(r.implied):
            ev.put(f"check.{r.Index}.{r.mode[:10]}.{r.level}.implied", r.implied, r.unit, r.check, "INFERENCE", "C")
            ev.put(f"check.{r.Index}.{r.mode[:10]}.{r.level}.ratio", r.ratio, "-", r.check, "INFERENCE", "C")
    ev.put("unsd_coke_industry_2019", coke_unsd, "kt", "UNdata 2019 ID coke-oven coke: consumption by iron and steel 520.3 + n.e.s. 57.8", "VERIFIED", "B")
    ev.extra["vectors_2050"] = {m: {k: v for k, v in V[m]["total"].items()} for m in V}
    ev.extra["unit_energy"] = dict(case3=c3, case4=c4)
    ev.write(cm.WORK / "evidence/_nickel_evidence.json")
    pd.set_option("display.width", 250)
    print(U.round(3).to_string()); print(CH.drop(columns=["note"]).round(3).to_string())
    print(c3, c4, "o2 el", o2_el)


if __name__ == "__main__":
    main()
