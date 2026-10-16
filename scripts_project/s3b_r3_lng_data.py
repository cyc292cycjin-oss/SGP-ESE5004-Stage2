"""S3B R3 (decision 68): LNG regasification terminal expansion and the Malaysia-Singapore pipeline capacity (registry fragment lng_r3).

Read-only search 2026-10-16 for public regasification terminal investment data with source, page and price year:
  * IGU World LNG Report 2024 (public PDF) and OIES NG149 "Floating LNG Update" (2019): HTTP 403 for automated fetch -> download list.
  * Ulvestad & Overland (2012), Int. J. Environ. Stud. 69(3):407-426, PMC3962073, section "LNG CAPEX": "highly site-specific, but a rough
    estimate might be $1 billion for every 10 million tpy" - no source and no price year.
  * ERIA RPR FY2016 No.7b Chapter 6 (PDF SHA 0952b487...): JPY 450 million per 1,000 t of LNG terminal (storage) capacity, storage sized at one
    week of demand (formula (1), PDF p.8, printed 73); Tables 22-23 (PDF p.4) print US$ figures that are evidently JPY (misprint).
  * PyPSA-Eur import branch 5a87cedd prepare_sector_network.py line 4561: terminal_capital_cost shipping-lch4 = 7018 EUR/MW/a, no source in the
    code or in Neumann et al. (2025) text / SI (searched).
The candidates span roughly US$80-670 per t/a (other secondary figures without a capacity basis), i.e. more than the +-50 % band, and none gives
a sourced unit cost with price year -> the fallback of the S3B instruction applies: main = no expansion (operating + under construction only,
proposed-only sites not built), the former 2.5 x cap at zero capex becomes the sensitivity (research.s3.gas.lng_expansion = cap_factor).
The candidates are registered as REFERENCE_ONLY with an indicative EUR2020/MW/a conversion for the user's decision.

    python scripts_project/s3b_r3_lng_data.py
"""
from __future__ import annotations

import pandas as pd

from d1_common import REG_DIR, ROOT, SRC_DIR, Registry, sha256, src_sha, write_csv, write_json

SCRIPT = "scripts_project/s3b_r3_lng_data.py"
FETCHED = "2026-10-16"
PE_IMPORT = SRC_DIR / "pypsa_eur_data" / "pypsa_eur_5a87cedd_prepare_sector_network.py"
DEFL = SRC_DIR / "A191RD3A086NBEA.csv"   # US GDP implicit price deflator (FRED), already in the intake
ERIA_SHA = "0952b4872356e19506cb809bbabd24d70659e8fbff4649b4378c533d3dbd9d99"
ERIA_URL = "https://www.eria.org/ERIA_RPR_FY2016_7b_Chapter_6.pdf"
PMC_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC3962073/"
DISCOUNT, LIFE, FOM = 0.07, 25.0, 0.035   # s2_costs.DISCOUNT; technology-data v0.15.0 'CH4 liquefaction' lifetime 25 a and FOM 3.5 %/a as the nearest LNG plant analogue
LNG = ROOT / "research_inputs/lng_terminals_v5/LNG_IMPORT_TERMINALS_GEM_2025.csv"
HOURS = 8760.0


def annuity(r, n):
    return r / (1.0 - (1.0 + r) ** -n)


def main():
    reg_df = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    fx = float(reg_df.loc["author_rule_fx_usd_eur_2020", "value"])   # EUR per USD, 2020 mean
    d = pd.read_csv(DEFL); d["year"] = d.observation_date.str[:4].astype(int); defl = d.set_index("year").A191RD3A086NBEA
    lng = pd.read_csv(LNG, keep_default_na=False); lng["cap"] = pd.to_numeric(lng.capacity_mwh_per_year, errors="coerce").fillna(0.0)
    q = lng[(pd.to_numeric(lng.capacity_mtpa, errors="coerce") > 0) & (lng.cap > 0)]
    LNG_MWH_PER_T = float((q.cap / (pd.to_numeric(q.capacity_mtpa) * 1e6)).median())   # the conversion used by the GEM terminal table itself (13.33 MWh/t)
    usd_per_tpa = 1e9 / 10e6   # Ulvestad & Overland: $1 billion per 10 million tpy
    price_year = 2011          # not stated in the paper; year before publication assumed for the indicative conversion only
    eur2020_per_tpa = usd_per_tpa * float(defl[2020] / defl[price_year]) * fx
    mw_per_tpa = LNG_MWH_PER_T / HOURS
    eur_per_mw = eur2020_per_tpa / mw_per_tpa
    eur_per_mw_a = eur_per_mw * (annuity(DISCOUNT, LIFE) + FOM)
    pe_text = PE_IMPORT.read_text().splitlines()
    assert "\"shipping-lch4\": 7018" in pe_text[4560], pe_text[4560]
    caps = []
    for node, g in lng.groupby("node"):
        if not node:
            continue
        ex = float(g[g.status.isin(["operating", "construction"])].cap.sum()) / HOURS; pr = float(g[g.status == "proposed"].cap.sum()) / HOURS
        caps.append(dict(node=node, country=str(g.country.iloc[0]) if "country" in g else "", existing_mw=ex, proposed_mw=pr, main_p_nom_max_mw=ex,
                         sensitivity_p_nom_max_mw=(2.5 * ex if ex > 0 else pr), h2_import_cap_mw=(2.5 * ex if ex > 0 else pr)))
    cdf = pd.DataFrame(caps)
    by_c = cdf.groupby("country")[["existing_mw", "proposed_mw", "main_p_nom_max_mw", "sensitivity_p_nom_max_mw"]].sum()
    out = ROOT / "research_inputs/lng_terminals_v5/LNG_EXPANSION_MODES_S3B_R3.csv"
    write_csv(cdf.to_dict("records"), out, list(cdf.columns))
    reg = Registry(SCRIPT)
    reg.add("lng_terminal_expansion_mode", "S3B R3 (decision 68): no public regasification terminal unit cost with source, page and price year was found within the +-50 % band "
            f"(search {FETCHED}: IGU World LNG Report 2024 and OIES NG149 not retrievable (HTTP 403, download list); Ulvestad & Overland 2012 rule of thumb without source or year; "
            "ERIA 2016 storage-based unit cost; PyPSA-Eur code constant without source) -> main = existing LNG import capacity only (GEM operating + under construction), "
            "proposed-only sites not built; the former 2.5 x cap at zero capex is the sensitivity research.s3.gas.lng_expansion = cap_factor", "existing_only", "flag", "C",
            "S3B instruction R3 (fallback)", "configs/research/baseline.yaml research.s3.gas.lng_expansion", sha256(LNG), decision_ref="68")
    reg.add("lng_regas_capex_ref_ulvestad_overland_2012", f"Regasification terminal capex rough estimate US$1 billion per 10 Mtpa = US$100 per t/a ('highly site-specific'; no source, no price year) - "
            f"indicative only: price year {price_year} assumed, x US GDP deflator 2020/{price_year} {float(defl[2020] / defl[price_year]):.4f} x {fx:.4f} EUR/USD = {eur2020_per_tpa:.1f} EUR2020 per t/a; "
            f"/ ({LNG_MWH_PER_T:.3f} MWh/t (GEM table conversion) / 8760 h) = {eur_per_mw:,.0f} EUR/MW; x (annuity 7 %/25 a + FOM 3.5 %) = {eur_per_mw_a:,.0f} EUR/MW/a", eur_per_mw_a, "EUR2020/MW/a", "C",
            "Ulvestad M., Overland I. (2012) Natural gas and CO2 price variation: impact on the relative cost-efficiency of LNG and pipelines, Int. J. Environ. Stud. 69(3):407-426, doi:10.1080/00207233.2012.677581",
            f"section 'LNG CAPEX' (PMC full text {PMC_URL}, fetched {FETCHED})", f"FRED deflator:{sha256(DEFL)}", decision_ref="68", status="REFERENCE_ONLY",
            sensitivity_low=0.5 * eur_per_mw_a, sensitivity_high=1.5 * eur_per_mw_a)
    reg.add("lng_regas_capex_ref_eria_2016", "ERIA (2016) LNG supply-chain investment: LNG terminal construction = capacity (1,000 t, storage sized at one week of demand) x JPY 450 million per 1,000 t "
            "(formula (1)); per t/a of throughput this is about JPY 8,650 (450e6 / 1,000 / 52); Tables 22-23 print 'US$100 billion' for an onshore terminal and 'US$50 billion' for a 5 MTPA terminal, "
            "evidently JPY (misprint) -> not converted", 450e6 / 1000 / 52, "JPY per t/a", "C",
            "ERIA Research Project Report FY2016 No.7b, Chapter 6 'Investment in LNG Supply Chain Infrastructure Estimation'", "PDF p.8 (printed 73) formula (1); PDF p.4 Tables 22-23",
            f"pdf:{ERIA_SHA} ({ERIA_URL}, fetched {FETCHED})", decision_ref="68", status="REFERENCE_ONLY")
    reg.add("lng_regas_capex_ref_pypsa_eur_import_branch", "PyPSA-Eur import branch terminal_capital_cost for shipping-lch4 = 7018 EUR/MW/a (code constant; no source in the code, nor in Neumann et al. 2025 "
            "text and SI); the liquid-H2 terminal cost 7018 x 1.2 (research.s3.imports.h2_terminal_capital_cost_eur_per_mw_a) uses it", 7018.0, "EUR/MW/a", "C",
            "PyPSA-Eur import branch 5a87cedd scripts/prepare_sector_network.py", "line 4561", sha256(PE_IMPORT), decision_ref="68", status="REFERENCE_ONLY")
    reg.add("gas_pipeline_MY_SG_capacity_search_s3b", f"S3B R3 search {FETCHED} for the Malaysia-Singapore Gas Pipeline (GEM P7105, 1991, 70 km) capacity: no public capacity found (GEM wiki capacity blank; "
            "Petronas PGU system 3,500 mmscfd is the whole Peninsular network; 1988 supply MoU >= 150 mmscfd and the 2012 Keppel 43 mmscfd are contract volumes, not capacity) -> "
            "gas_pipeline_existing_malaysia_singapore stays DATA_PENDING; only the MY_Peninsular2 1 - SG2 0 corridor candidate exists", None, "MW_NCV", "C",
            "GEM wiki Malaysia Singapore Gas Pipeline; Petronas Gas Berhad gas transportation page", "search log; GEM_GGIT_GAS_PIPELINES_ASEAN.csv row P7105 capacity empty", src_sha("GEM_GGIT_GAS_PIPELINES_ASEAN.csv"), country="MY-SG", decision_ref="68", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "lng_r3.csv")
    ev = dict(script=SCRIPT, fetched=FETCHED, fx_eur_per_usd_2020=fx, deflator_2020_over_2011=float(defl[2020] / defl[price_year]), lng_mwh_per_t=LNG_MWH_PER_T,
              annuity=annuity(DISCOUNT, LIFE), fom=FOM, ulvestad=dict(usd_per_tpa=usd_per_tpa, eur2020_per_tpa=eur2020_per_tpa, eur_per_mw=eur_per_mw, eur_per_mw_a=eur_per_mw_a),
              eria=dict(jpy_per_kt_storage=450e6, jpy_per_tpa_throughput=450e6 / 1000 / 52, sha256=ERIA_SHA, url=ERIA_URL), pypsa_eur_constant_eur_per_mw_a=7018.0,
              caps_by_country_mw=by_c.round(3).to_dict("index"), caps_total_mw=by_c.sum().round(3).to_dict())
    write_json(ev, ROOT / "research_inputs/lng_terminals_v5/LNG_EXPANSION_EVIDENCE_S3B_R3.json")
    print(by_c.round(1).to_string()); print("total", by_c.sum().round(1).to_dict()); print("ulvestad EUR/MW/a", round(eur_per_mw_a))


if __name__ == "__main__":
    main()
