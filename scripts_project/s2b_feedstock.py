"""R2 (decision 56, S2 supplement 02): chemical feedstock carbon on a territorial basis.

Territorial emissions (counted in the country where they occur):
  (a) process emissions of the chemical industry and non-energy products: EDGAR 2025 2.B + 2.D (2019) x industry
      multiplier (R3) -> process-emission bus (capturable by process CC);
  (b) domestic end-of-life plastics burned: What a Waste 3.0 MSW 2050 x plastic share x (incineration share +
      uncollected share x open-burned share of the uncollected) x IPCC 2006 Vol.5 Ch.2 Table 2.4 plastics
      (dry matter 100 %, total carbon 75 % of dry weight, fossil fraction 100 %) x 44/12 -> atmosphere;
  (c) exported products and landfilled plastics are not counted (IPCC: landfilled plastic carbon is stored).
The former PyPSA-Eur default (all feedstock carbon released, HVC_environment_sequestration_fraction 0) is
kept as the sensitivity mode research.s2.industry.feedstock_carbon_mode = full_release.

    python scripts_project/s2b_feedstock.py
"""
from __future__ import annotations

import pandas as pd

from d1_common import ASEAN, DEMAND_DIR, REG_DIR, ROOT, SRC_DIR, Registry, read_csv, sha256, src_sha, write_csv, write_json

SCRIPT = "scripts_project/s2b_feedstock.py"
EDGAR = "EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv"
WAW = "WHAT_A_WASTE_3_ASEAN11_COUNTRY.csv"
IPCC = "IPCC2006_V5_Ch2_WasteData.pdf"
ALLOCATIONS = {"aeo8_ats_relative": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", "gdp": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_GDP_SENSITIVITY.csv",
               "population": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_POP_SENSITIVITY.csv"}
PLASTIC_DM, PLASTIC_C, PLASTIC_FOSSIL = 1.00, 0.75, 1.00     # IPCC 2006 Vol.5 Ch.2 Table 2.4, row Plastics (ranges: C 67-85 %, fossil 95-100 %)
PLASTIC_C_LOW, PLASTIC_C_HIGH, PLASTIC_FOSSIL_LOW = 0.67, 0.85, 0.95
CO2_PER_C = 44.0 / 12.0
# PyPSA-Eur full-release accounting as implemented in S2 (s2_layers.add_demand_layer): feedstock x EF x end-of-life release 1.0; oil x HVC primary fraction
EF = {"coal": 0.3361, "oil": 0.2571, "gas": 0.198}


def pct(v):
    return float(v) if str(v).strip() not in ("", "nan") else None


def main():
    ed = pd.read_csv(SRC_DIR / EDGAR); ed_sha = src_sha(EDGAR)
    waw = {r["ISO2"]: r for r in read_csv(SRC_DIR / WAW)}; waw_sha = src_sha(WAW)
    ipcc_sha = src_sha(IPCC)
    reg_df = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    hvc_primary = float(reg_df.loc["share_HVC_primary_fraction_2050", "value"])
    bound = pd.read_csv(REG_DIR / "FEEDSTOCK_CARBON_BOUNDARY_2019.csv").set_index("country")
    def edgar(c, code):
        v = ed[(ed.iso == c) & (ed.ipcc_code_2006_for_standard_report == code)].kt_CO2_2019
        return float(v.fillna(0.0).sum()) * 1e3
    # S3-0 (decision 63): missing What a Waste fields -> MSW-2050-weighted mean of the ASEAN countries with data (grade C); sensitivity 0 .. observed maximum
    def wmean(field):
        vals = [(c, pct(waw[c].get(field)), pct(waw[c].get("MSW generation - projected 2050 (t/y)"))) for c in ASEAN if c in waw]
        vals = [(c, v, w) for c, v, w in vals if v is not None and w]
        if not vals:
            return None, None, []
        return sum(v * w for _, v, w in vals) / sum(w for _, _, w in vals), max(v for _, v, _ in vals), [c for c, _, _ in vals]
    plastic_proxy, plastic_max, plastic_from = wmean("Composition - plastic (% weight MSW)")
    ob_proxy, ob_max, ob_from = wmean("Uncollected - open burned  (% population uncollected)")
    proxies = dict(plastic_share=dict(value=plastic_proxy, observed_max=plastic_max, countries=plastic_from), open_burned_share_of_uncollected=dict(value=ob_proxy, observed_max=ob_max, countries=ob_from))
    tables = {}
    for mode, fname in ALLOCATIONS.items():
        dem = pd.read_csv(DEMAND_DIR / fname, keep_default_na=False)
        rows = []
        for c in ASEAN:
            d = dem[(dem.country == c) & (dem.sector == "Industry")]
            mult = float(d.multiplier_total.iloc[0]) if len(d) else 1.0
            b2, d2 = edgar(c, "2.B"), edgar(c, "2.D")
            w = waw.get(c, {})
            msw50 = pct(w.get("MSW generation - projected 2050 (t/y)")) or 0.0
            plastic = pct(w.get("Composition - plastic (% weight MSW)"))
            inc = pct(w.get("Treatment - incineration (% weight MSW generated)"))
            unc = pct(w.get("Treatment - uncollected (% weight MSW generated)"))
            ob = pct(w.get("Uncollected - open burned  (% population uncollected)"))
            flags = []; plastic_is_proxy = ob_is_proxy = False
            if plastic is None and plastic_proxy is not None:
                plastic = plastic_proxy; plastic_is_proxy = True
                flags.append(f"plastic_share_proxy = MSW-2050-weighted mean of {'+'.join(plastic_from)} (decision 63, grade C; sensitivity 0..{plastic_max:.3f})")
            elif plastic is None:
                flags.append("plastic_share_missing (What a Waste composition empty) -> DATA_PENDING, plastics term = 0")
            if inc is None:
                flags.append("incineration_share_missing -> 0")
            if unc is None:
                flags.append("uncollected_share_missing -> 0")
            elif ob is None and ob_proxy is not None:
                ob = ob_proxy; ob_is_proxy = True
                flags.append(f"open_burned_share_proxy = MSW-2050-weighted mean of {'+'.join(ob_from)} (decision 63, grade C; sensitivity 0..{ob_max:.3f})")
            elif ob is None:
                flags.append("open_burned_share_of_uncollected_missing -> 0 (uncollected waste exists but its burning share is not reported)")
            burned = (inc or 0.0) + (unc or 0.0) * (ob or 0.0)
            plastic_t = msw50 * (plastic or 0.0)
            co2_plastics = plastic_t * burned * PLASTIC_DM * PLASTIC_C * PLASTIC_FOSSIL * CO2_PER_C
            co2_plastics_low = plastic_t * burned * PLASTIC_DM * PLASTIC_C_LOW * PLASTIC_FOSSIL_LOW * CO2_PER_C
            co2_plastics_high = plastic_t * burned * PLASTIC_DM * PLASTIC_C_HIGH * PLASTIC_FOSSIL * CO2_PER_C
            # decision 63 proxy sensitivity: proxies at 0 (low) and at the observed ASEAN maximum (high)
            pl_lo, pl_hi = (0.0, plastic_max) if plastic_is_proxy else (plastic or 0.0, plastic or 0.0)
            ob_lo, ob_hi = (0.0, ob_max) if ob_is_proxy else ((ob or 0.0), (ob or 0.0))
            co2_proxy_low = msw50 * pl_lo * ((inc or 0.0) + (unc or 0.0) * ob_lo) * PLASTIC_DM * PLASTIC_C * PLASTIC_FOSSIL * CO2_PER_C
            co2_proxy_high = msw50 * pl_hi * ((inc or 0.0) + (unc or 0.0) * ob_hi) * PLASTIC_DM * PLASTIC_C * PLASTIC_FOSSIL * CO2_PER_C
            proc = (b2 + d2) * mult
            ne = dem[(dem.country == c) & (dem.sector == "NonEnergyUse")]
            full = 0.0
            for car, v in ne.groupby("carrier").value_2050_mwh.sum().items():
                vv = float(pd.to_numeric(v, errors="coerce") or 0.0) if not isinstance(v, (int, float)) else float(v)
                full += vv * EF.get(car, 0.0) * (hvc_primary if car == "oil" else 1.0)
            rows.append(dict(country=c, industry_multiplier=mult, edgar_2B_2019_t=b2, edgar_2D_2019_t=d2, process_2B_2D_2050_t=proc,
                             msw_2050_t=msw50, plastic_share=plastic if plastic is not None else "", incineration_share=inc if inc is not None else "",
                             uncollected_share=unc if unc is not None else "", open_burned_share_of_uncollected=ob if ob is not None else "",
                             plastic_share_is_proxy=plastic_is_proxy, open_burned_share_is_proxy=ob_is_proxy,
                             burned_share_total=burned, plastic_waste_2050_t=plastic_t, plastics_burned_co2_2050_t=co2_plastics,
                             plastics_burned_co2_low_t=co2_plastics_low, plastics_burned_co2_high_t=co2_plastics_high,
                             plastics_burned_co2_proxy_low_t=co2_proxy_low, plastics_burned_co2_proxy_high_t=co2_proxy_high,
                             territorial_total_2050_t=proc + co2_plastics, full_release_2050_t=full, difference_full_minus_territorial_t=full - (proc + co2_plastics),
                             feedstock_potential_2019_t=float(bound.at[c, "feedstock_carbon_potential_tco2"]) if c in bound.index else 0.0,
                             edgar_2B_2D_4C_2019_t=float(bound.at[c, "edgar_2B_2D_4C_total_tco2"]) if c in bound.index else 0.0, flags="; ".join(flags)))
        tables[mode] = rows
        write_csv(rows, REG_DIR / f"FEEDSTOCK_CARBON_TERRITORIAL_2050_{mode}.csv", list(rows[0].keys()))
    # ---- registry (main allocation) ------------------------------------------------------------------------------
    reg = Registry(SCRIPT)
    reg.add("feedstock_carbon_mode", "Main feedstock-carbon accounting = territorial (R2, decision 56): EDGAR 2.B+2.D x industry multiplier on the process bus + domestic plastics burned to air; "
            "full_release (PyPSA-Eur default, all feedstock carbon emitted) kept as sensitivity switch research.s2.industry.feedstock_carbon_mode", "territorial", "flag", "B",
            "S2 supplement 02 R2", "configs/research/baseline.yaml", ed_sha, decision_ref="56")
    reg.add("plastics_total_carbon_fraction_ipcc", "Plastics total carbon content in % of dry weight (default 75, range 67-85)", PLASTIC_C, "fraction", "B",
            "IPCC 2006 Guidelines Vol.5 Ch.2 Waste Generation, Composition and Management Data", "Table 2.4 (p.2.14), row Plastics", ipcc_sha, sensitivity_low=PLASTIC_C_LOW, sensitivity_high=PLASTIC_C_HIGH, decision_ref="56")
    reg.add("plastics_fossil_carbon_fraction_ipcc", "Plastics fossil carbon fraction in % of total carbon (default 100, range 95-100)", PLASTIC_FOSSIL, "fraction", "B",
            "IPCC 2006 Guidelines Vol.5 Ch.2", "Table 2.4 (p.2.14), row Plastics", ipcc_sha, sensitivity_low=PLASTIC_FOSSIL_LOW, sensitivity_high=1.0, decision_ref="56")
    reg.add("plastics_dry_matter_ipcc", "Plastics dry matter content in % of wet weight (default 100)", PLASTIC_DM, "fraction", "B", "IPCC 2006 Guidelines Vol.5 Ch.2", "Table 2.4 (p.2.14), row Plastics", ipcc_sha, decision_ref="56")
    reg.add("plastics_landfill_carbon_treatment", "Landfilled and exported plastic carbon is not counted as a domestic emission (IPCC: carbon in SWDS plastics is stored, no CO2); incineration with energy recovery counts as emission, "
            "the recovered energy is not modelled in this round", "NOT_COUNTED", "method", "B", "IPCC 2006 Vol.5 Ch.2 Section 2.3.3 and Ch.3; S2 supplement 02 R2(c)", "Ch.2 p.2.14 note on fossil carbon in plastics", ipcc_sha, decision_ref="56")
    main = tables["aeo8_ats_relative"]
    for r in main:
        c = r["country"]; w = waw.get(c, {})
        reg.add(f"feedstock_process_2B_2D_2050_{c}", f"{c} chemical-industry process CO2 (2.B {r['edgar_2B_2019_t']:.4g} t) + non-energy products (2.D {r['edgar_2D_2019_t']:.4g} t) 2019 x industry multiplier {r['industry_multiplier']:.4f}; loaded on the process-emission bus (R2)",
                r["process_2B_2D_2050_t"], "tCO2/a", "B", "EDGAR 2025 x D1/R3 industry multiplier", "codes 2.B, 2.D (2019); s2b_feedstock.py", ed_sha, country=c, decision_ref="56",
                status="REGISTERED" if r["process_2B_2D_2050_t"] > 0 else "SOURCE_ZERO")
        src_w = f"What a Waste 3.0 country dataset (raw2/What_a_Waste_3.0_COUNTRY_Dataset_&_Codebook.xlsx -> extraction {WAW})"
        if r["plastic_share"] == "":
            reg.add(f"waste_plastic_share_{c}", f"{c} plastic share of MSW not reported in What a Waste 3.0 -> plastics term not estimated", None, "fraction", "B", src_w, "Composition - plastic (% weight MSW)", waw_sha, country=c, decision_ref="56", status="DATA_PENDING")
        elif r["plastic_share_is_proxy"]:
            reg.add(f"waste_plastic_share_{c}", f"{c} plastic share of MSW not reported -> proxy = MSW-2050-weighted mean of {'+'.join(plastic_from)} (decision 63); sensitivity 0 .. observed max {plastic_max:.3f}", r["plastic_share"], "fraction", "C",
                    src_w + " (ASEAN countries with data)", "Composition - plastic (% weight MSW); s2b_feedstock.py wmean", waw_sha, country=c, decision_ref="56,63", sensitivity_low=0.0, sensitivity_high=plastic_max)
        else:
            reg.add(f"waste_plastic_share_{c}", f"{c} plastic share of MSW (weight)", r["plastic_share"], "fraction", "B", src_w, "Composition - plastic (% weight MSW)", waw_sha, country=c, decision_ref="56")
        reg.add(f"waste_msw_2050_{c}", f"{c} MSW generation projected 2050", r["msw_2050_t"], "t/a", "B", src_w, "MSW generation - projected 2050 (t/y)", waw_sha, country=c, decision_ref="51,56")
        reg.add(f"waste_incineration_share_{c}", f"{c} share of generated MSW incinerated" + (" (not reported -> 0)" if r["incineration_share"] == "" else ""), r["incineration_share"] if r["incineration_share"] != "" else 0.0, "fraction", "B", src_w,
                "Treatment - incineration (% weight MSW generated)", waw_sha, country=c, decision_ref="56", status="REGISTERED" if r["incineration_share"] != "" else "SOURCE_ZERO")
        reg.add(f"waste_uncollected_open_burned_share_{c}", f"{c} uncollected share of MSW {r['uncollected_share'] if r['uncollected_share'] != '' else 'n/a'} x open-burned share of the uncollected population {r['open_burned_share_of_uncollected'] if r['open_burned_share_of_uncollected'] != '' else 'n/a'} "
                "(population share used as a proxy for the waste share, INFERENCE)" + (f"; open-burned share = proxy, MSW-2050-weighted mean of {'+'.join(ob_from)} (decision 63), sensitivity 0 .. observed max {ob_max:.3f}" if r["open_burned_share_is_proxy"] else ""),
                (r["uncollected_share"] or 0.0) * (r["open_burned_share_of_uncollected"] or 0.0) if (r["uncollected_share"] != "" and r["open_burned_share_of_uncollected"] != "") else 0.0,
                "fraction", "C", src_w, "Treatment - uncollected; Uncollected - open burned", waw_sha, country=c, decision_ref="56,63" if r["open_burned_share_is_proxy"] else "56", sensitivity_low=0.0,
                sensitivity_high=((r["uncollected_share"] or 0.0) * (ob_max if r["open_burned_share_is_proxy"] else 1.0)) if r["uncollected_share"] != "" else 0.0,
                status="REGISTERED" if (r["uncollected_share"] != "" and r["open_burned_share_of_uncollected"] != "") else ("DATA_PENDING" if r["uncollected_share"] != "" else "SOURCE_ZERO"))
        reg.add(f"feedstock_plastics_burned_co2_2050_{c}", f"{c} domestic end-of-life plastics burned 2050: MSW {r['msw_2050_t']:.4g} t x plastic {r['plastic_share'] or 0} x burned share {r['burned_share_total']:.4f} x C 0.75 x fossil 1.0 x 44/12" + (f"; flags: {r['flags']}" if r["flags"] else ""),
                r["plastics_burned_co2_2050_t"], "tCO2/a", "B", "What a Waste 3.0 x IPCC 2006 Vol.5 Table 2.4", "s2b_feedstock.py", f"{waw_sha}|{ipcc_sha}", country=c, decision_ref="56",
                sensitivity_low=min(r["plastics_burned_co2_low_t"], r["plastics_burned_co2_proxy_low_t"]), sensitivity_high=max(r["plastics_burned_co2_high_t"], r["plastics_burned_co2_proxy_high_t"]),
                status="REGISTERED" if r["plastics_burned_co2_2050_t"] > 0 else "SOURCE_ZERO")
        reg.add(f"feedstock_full_release_2050_{c}", f"{c} full-release feedstock carbon 2050 (PyPSA-Eur default as implemented in S2: non-energy use x EF, oil x HVC primary {hvc_primary}); sensitivity mode", r["full_release_2050_t"], "tCO2/a", "C",
                "derived (D1 demand table x technology-data CO2 intensities)", "s2b_feedstock.py", ed_sha, country=c, decision_ref="56", sensitivity_low=r["territorial_total_2050_t"], sensitivity_high=r["full_release_2050_t"], status="SENSITIVITY")
    reg.write(REG_DIR / "fragments" / "feedstock_territorial.csv")
    write_json(dict(script=SCRIPT, sources=dict(edgar=ed_sha, what_a_waste=waw_sha, ipcc_v5_ch2=ipcc_sha), constants=dict(plastic_dry_matter=PLASTIC_DM, plastic_carbon=PLASTIC_C, plastic_fossil=PLASTIC_FOSSIL, hvc_primary=hvc_primary, ef=EF),
                    decision_63_proxies=proxies, main=main), REG_DIR / "FEEDSTOCK_CARBON_TERRITORIAL_EVIDENCE.json")
    df = pd.DataFrame(main).set_index("country")
    print((df[["process_2B_2D_2050_t", "plastics_burned_co2_2050_t", "territorial_total_2050_t", "full_release_2050_t"]] / 1e6).round(2).to_string())
    print(df[["plastic_share", "burned_share_total", "flags"]].to_string())


if __name__ == "__main__":
    main()
