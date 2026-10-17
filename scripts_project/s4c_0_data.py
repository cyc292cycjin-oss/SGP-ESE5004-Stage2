"""S4C-0 data (S4C instruction v1, 2026-10-16; decisions 85, 86, 90): registry fragment s4c_0 and the finance tables.

    python scripts_project/s4c_0_data.py

Writes
  * research_inputs/finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv - country cost-of-capital values from public sources (IEA Cost of Capital
    Observatory dashboard, 2025 survey update, tables as published: weighted average cost of capital, nominal, post-tax, local currency,
    rounded to 0.5 pp, * = indicative) plus one model row per ASEAN country (wacc_real for research.finance.wacc_mode country_specific).
    The model annualises real EUR2020 costs with a real rate; no source gives a real ASEAN rate, so every model row is DATA_PENDING
    (no estimate: a nominal-to-real conversion would need a country inflation assumption, left to the user).
  * research_inputs/finance_v5/DISCOUNT_RATE_IN_USE.csv - where the model's discount rate acts (cost-layer rows, appended rows, stock).
  * research_inputs/registry_v5/fragments/s4c_0.csv
"""
from __future__ import annotations

import io
import re

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv

SCRIPT = "scripts_project/s4c_0_data.py"
INSTRUCTION_SHA = "e1bad922b036bcb425cb9b77853e5cc4f9ca771c59c90da1a23321b89a1dcdd3"   # S4C_CLAUDE_CODE_INSTRUCTION.md v1 (decisions 82-90)
FIN = ROOT / "research_inputs" / "finance_v5"
IEA_DASH = FIN / "sources" / "IEA_CoC_Observatory_dashboard_2025.html"
IEA_COMM = FIN / "sources" / "IEA_commentary_SEA_cost_of_capital_20251008.html"
IEA_DASH_URL = "https://www.iea.org/reports/cost-of-capital-observatory/dashboard-2"
IEA_COMM_URL = "https://www.iea.org/commentaries/high-cost-of-capital-and-limited-project-pipeline-hinder-clean-energy-investment-in-southeast-asia"
FETCHED_UTC = "2026-10-16T13:57:17Z"
COST_LAYER = ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020_prepared.csv"
WEO_CSV = REG_DIR / "sources" / "WEO2025_FOSSIL_PRICES.csv"
PE_PSN = REG_DIR / "sources" / "pypsa_eur_v2025.07.0_prepare_sector_network.py"
ASEAN = ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN"]
NAMES = {"Indonesia": "ID", "Viet Nam": "VN", "Philippines": "PH", "Malaysia": "MY", "Thailand": "TH"}
# dashboard tables in page order (headings of the page: solar PV 50/100 MW, batteries 40 MW, gas fired 250 MW, hydro 150 MW; offshore wind table
# without a heading tag); identified by their year rows and by the commentary text (solar 2024 medians 9.4 / 9.0 / 8.0 %)
TABLE_TECH = {0: "solar PV 50-100 MW", 1: "gas fired 250 MW", 2: "utility-scale batteries 40 MW", 3: "offshore wind 250 MW (expected, no FID yet)", 4: "hydropower 150 MW"}


def _range(cell):
    s = str(cell).strip()
    if s in ("-", "nan", ""):
        return None
    ind = s.endswith("*"); nums = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)%?", s.replace("*", ""))]
    lo, hi = (nums[0], nums[-1]) if nums else (None, None)
    return dict(low=lo / 100.0, high=hi / 100.0, indicative=ind, cell=s)


def iea_rows():
    tables = pd.read_html(io.StringIO(IEA_DASH.read_text(encoding="utf-8")))
    rows = []
    for i, tech in TABLE_TECH.items():
        t = tables[i]; t.columns = [c[-1] for c in t.columns]
        for _, r in t.iterrows():
            for name, iso in NAMES.items():
                if name not in t.columns:
                    continue
                v = _range(r[name])
                if v is None:
                    continue
                rows.append(dict(country=iso, technology=tech, fid_year=int(r["Year of investment decision"]), wacc_low=v["low"], wacc_high=v["high"], indicative=v["indicative"],
                                 published_cell=v["cell"], basis="nominal, post-tax, local currency (IEA: weighted average cost of capital, nominal post tax; rounded to 0.5 pp)",
                                 source="IEA Cost of Capital Observatory, Dashboard (2025 survey update)", source_url=IEA_DASH_URL, source_sha256=sha256(IEA_DASH), fetched_utc=FETCHED_UTC,
                                 wacc_real="", status="REFERENCE_ONLY", note=""))
    return rows


def main():
    FIN.mkdir(parents=True, exist_ok=True)
    rows = iea_rows()
    solar24 = {r["country"]: r for r in rows if r["technology"].startswith("solar") and r["fid_year"] == 2024}
    comm = IEA_COMM.read_text(encoding="utf-8")
    medians = dict(ID=0.094, VN=0.090, PH=0.080)
    if "9.4%, 9.0% and 8.0% respectively in 2024" not in comm:
        raise SystemExit("IEA commentary text changed: solar 2024 medians not found")
    for c, v in medians.items():
        rows.append(dict(country=c, technology="solar PV (utility-scale), median of survey responses", fid_year=2024, wacc_low=v, wacc_high=v, indicative=(c == "PH"), published_cell=f"{v:.1%}",
                         basis="nominal, post-tax, local currency (IEA commentary)", source="IEA commentary 'High cost of capital and limited project pipeline hinder clean energy investment in Southeast Asia' (Teng & Erdogan, 2025-10-08)",
                         source_url=IEA_COMM_URL, source_sha256=sha256(IEA_COMM), fetched_utc=FETCHED_UTC, wacc_real="", status="REFERENCE_ONLY", note="text: 9.4 %, 9.0 % and 8.0 % (ID, VN, PH) in 2024"))
    for c in ASEAN:
        have = sorted({r["technology"] for r in rows if r["country"] == c})
        note = ("only nominal post-tax local-currency values are published (IEA); the model annualises real EUR2020 costs, so a real rate would need a country inflation assumption - not estimated, user decision"
                if have else "no public country estimate found (IEA Cost of Capital Observatory covers ID, VN, PH, MY, TH; IRENA 2023 'The cost of financing for renewable power' not retrievable: irena.org HTTP 403, mirror 404)")
        rows.append(dict(country=c, technology="model (all new-build technologies)", fid_year="", wacc_low="", wacc_high="", indicative="", published_cell="", basis="real (model basis: annuity on constant EUR2020 costs)",
                         source="", source_url="", source_sha256="", fetched_utc="", wacc_real="", status="DATA_PENDING", note=note))
    cols = ["country", "technology", "fid_year", "wacc_low", "wacc_high", "indicative", "published_cell", "basis", "wacc_real", "status", "source", "source_url", "source_sha256", "fetched_utc", "note"]
    write_csv(rows, FIN / "COUNTRY_WACC_PUBLIC_SOURCES.csv", cols)
    # discount rate in use (decision 90 item 1)
    c = pd.read_csv(COST_LAYER, index_col=0)
    dr = c["discount rate"]
    low = sorted(dr.index[dr != 0.07])
    use = [dict(scope="cost layer technology-data v0.15.0 2050 EUR2020 (decision 50): every prepared row except below", rows=int((dr == 0.07).sum()), discount_rate=0.07,
                source="technology-data has no discount rate for these rows; prepare step fills 'discount rate' 0.07 (pypsa-asean configs/config.default.yaml costs.fill_values line 579; scripts_project/s2_0_cost_layer_v015.py FILL)",
                acts_on="annualised investment of every new-build component priced from the layer (fixed = (annuity(lifetime, r) + FOM) x investment)", basis="real (annuity on constant EUR2020 costs; INFERENCE from the price basis)"),
           dict(scope="cost layer rows with their own technology-data discount rate: " + "; ".join(low), rows=len(low), discount_rate=0.04,
                source="technology-data v0.15.0 costs_2050.csv parameter 'discount rate' 0.04 ('standard for decentral' / Palzer thesis, from old pypsa cost assumptions)",
                acts_on="solar rooftop candidates once priced from the layer (S4C-1); the decentral heat rows are not built", basis="as published"),
           dict(scope="appended rows nuclear SMR (decision 46) and geothermal (decision 52)", rows=2, discount_rate=0.07, source="scripts_project/s2_costs.py DISCOUNT = 0.07",
                acts_on="SMR and geothermal candidates", basis="same as the layer"),
           dict(scope="frozen electric base candidates (onwind, offwind, solar, solar rooftop, AC lines, DC links) before S4C-1", rows="", discount_rate=0.07,
                source="author chain: pypsa-asean scripts/process_cost_data.py line 454 annuity(lifetime, 'discount rate') with costs.fill_values 0.07; costs.discountrate [0.071] (config.default.yaml line 560) only names sector prenetworks",
                acts_on="replaced by the cost layer in S4C-1 for wind and solar (decision 82)", basis="as the author chain"),
           dict(scope="existing stock (frozen base, GEM additions, existing cross-border capacity)", rows="", discount_rate="none",
                source="non-extendable stock has capital_cost 0 and an annual fixed O&M constant (existing_annual_fixed_om_eur); existing capacity of extendable lines / links / LNG carries no new capex (decision 48; PyPSA objective constant)",
                acts_on="no annuity: the discount rate does not act on the stock", basis="-")]
    write_csv(use, FIN / "DISCOUNT_RATE_IN_USE.csv", list(use[0].keys()))
    # ---------------------------------------------------------------- registry fragment
    reg = Registry(SCRIPT); weo_sha = sha256(WEO_CSV); cfg = "configs/research/baseline.yaml"
    reg.add("fuel_price_scenario_main", "Decision 85 (modifies decision 33 after seeing the smoke results): fossil fuel prices of the main run = WEO 2025 Table 2.3 STEPS 2050 for gas, oil and coal "
            "(one scenario for all three, asserted at build by s4c_layers.check_fuel_prices); reason: price-quantity consistency - ASEAN is a price taker on the world gas market and "
            "national net zero in ASEAN does not imply the global NZE; NZE 2050 is the low-price sensitivity, CPS 2050 an optional value; domestic gas production at the same price (decision 43)",
            "steps", "flag", "B", "S4C instruction S4C-0 item 1; IEA WEO 2025 Table 2.3", f"{cfg} research.fuels.price_scenario", f"instruction:{INSTRUCTION_SHA}|weo_extraction:{weo_sha}", decision_ref="33, 85")
    reg.add("fuel_price_regasification_adder_s4c", "LNG regasification adder stays DATA_PENDING under the STEPS main price (registry fuel_price_lng_regasification_adder)", None, "EUR2020/MWh", "C",
            "S4C instruction S4C-0 item 1", "fuel_price_lng_regasification_adder", INSTRUCTION_SHA, decision_ref="85", status="DATA_PENDING")
    reg.add("lng_upstream_emissions_out_of_scope", "To be discussed later (decision 85): upstream methane and supply-chain emissions of imported LNG are not counted under territorial accounting "
            "(only combustion in the consuming country and the fugitive factor of domestic production are booked)", "not_counted", "flag", "B", "S4C instruction S4C-0 item 1", "-", INSTRUCTION_SHA,
            decision_ref="85", status="REFERENCE_ONLY")
    btl_fixed, btl_eff = float(c.at["BtL", "fixed"]), float(c.at["BtL", "efficiency"])
    reg.add("btl_capital_cost_x_efficiency", f"Decision 86 a: BtL capital cost per MW biomass input = technology-data v0.15.0 BtL fixed {btl_fixed:,.1f} x efficiency {btl_eff} as PyPSA-Eur v2025.07.0 "
            "prepare_sector_network.py lines 4230-4231 (S4B report cited 4227-4228; corrected); former model 252,723 EUR/MW_biomass/a", btl_fixed * btl_eff, "EUR2020/MW_biomass/a", "B",
            "PyPSA-Eur v2025.07.0 scripts/prepare_sector_network.py; technology-data v0.15.0 BtL", "lines 4230-4231 (capital_cost = BtL capital_cost x BtL efficiency)", f"psn:{sha256(PE_PSN)}|layer:{sha256(COST_LAYER)}", decision_ref="86")
    reg.add("limitation_electricity_grid_connection", "Decision 86 a: PyPSA-Eur electricity_grid_connection (config line 746) stays not applied - technology-data v0.15.0 (decision 50) has no 'electricity grid connection' row; "
            "registered as a limitation (onshore wind / solar candidates carry no separate grid-connection cost)", "not_applied", "flag", "C", "S4C instruction S4C-0 item 2 a", "sector_deviation_electricity_grid_connection", INSTRUCTION_SHA,
            decision_ref="86", status="REFERENCE_ONLY")
    reg.add("limitation_pipeline_compression", "Decision 86 a: H2 / gas pipeline compression electricity (PyPSA-Eur 0.018 / 0.01 MWh_el per MWh per 1000 km, config lines 756-761) stays not modelled (bidirectional lossless links); "
            "registered as a limitation (0.2-2.3 % of the transported energy)", "not_modelled", "flag", "C", "S4C instruction S4C-0 item 2 a", "sector_deviation_pipeline_compression", INSTRUCTION_SHA, decision_ref="86", status="REFERENCE_ONLY")
    reg.add("candidate_pipeline_statuses_confirmed", "Decision 86 b: project-pipeline cap of the hydro / geothermal / PHS candidates = GEM announced + pre-construction (main, as implemented in S4B-2; construction units are 2050 stock, decision 77)",
            "announced_preconstruction", "flag", "B", "S4C instruction S4C-0 item 2 b", f"{cfg} research.candidates.pipeline_cap_statuses", INSTRUCTION_SHA, decision_ref="78, 86")
    reg.add("tests_gate4_activation_accepted_state", "Decision 86 c: the four test_gate4_activation tests assert the accepted state (17 NEC source rows, 171 accepted 2050 demands, PH rail accepted, NUMERIC_INPUT_READY true), "
            "citing 0177f678 and GATE4-20261006-FINAL-CLOSURE; no xfail", "updated", "flag", "B", "S4C instruction S4C-0 item 2 c", "tests/research/test_gate4_activation.py", INSTRUCTION_SHA, decision_ref="86", status="REFERENCE_ONLY")
    reg.add("download_declined_wdpa_full", "Decision 86 d: full-resolution WDPA (2026-10 shp 4.68 GB / gdb 2.00 GB) not downloaded; protected areas stay the local natura.tiff (2.5 arcmin)", "not_downloaded", "flag", "B",
            "S4C instruction S4C-0 item 2 d", "S4B DOWNLOAD_LIST.csv", INSTRUCTION_SHA, decision_ref="86", status="REFERENCE_ONLY")
    reg.add("download_declined_dea_2026_xlsx", "Decision 86 d: DEA 2026 technology data workbook not downloaded; the onshore turbine uses the technology-data v0.15.0 cited DEA sheet", "not_downloaded", "flag", "B",
            "S4C instruction S4C-0 item 2 d", "S4B DOWNLOAD_LIST.csv", INSTRUCTION_SHA, decision_ref="86", status="REFERENCE_ONLY")
    reg.add("synthetic_methane_cross_border_accounting_accepted", "Decision 86 e: synthetic methane keeps the decision-64 gas producer-credit accounting across borders (credit in the capture country, fossil EF where it is burned)",
            "accepted", "flag", "B", "S4C instruction S4C-0 item 2 e", "S4B report section 0.1", INSTRUCTION_SHA, decision_ref="64, 86")
    reg.add("acceptance_column_dual_sign_scale_confirmed", "Decision 84 d / 86 f (S4B section 8 item 2): A1/A2 column dual-sign error measured on the stationarity scale max(1, |c| + |a|'|pi| + |rc|); "
            "chosen after seeing the S3B/S4A values (stated); the V4 form max(1, |rc|) is reported alongside", "stationarity_scale", "flag", "B", "S4C instruction S4C-0 item 2 f",
            f"{cfg} research.solver.interior.column_dual_sign_scale", INSTRUCTION_SHA, decision_ref="84, 86")
    reg.add("discount_rate_uniform_main", "Decision 90: the main run keeps one discount rate for all countries (social-planner view): 0.07 (technology-data / pypsa-asean fill value; real basis, INFERENCE) on every cost-layer row "
            f"except {len(low)} decentral rows incl. solar-rooftop at 0.04 (technology-data own value), SMR and geothermal 0.07 (s2_costs.DISCOUNT); stock carries no annuity (research_inputs/finance_v5/DISCOUNT_RATE_IN_USE.csv)",
            0.07, "per unit", "B", "technology-data v0.15.0; pypsa-asean config.default.yaml costs.fill_values (line 579)", "research_inputs/finance_v5/DISCOUNT_RATE_IN_USE.csv", sha256(FIN / "DISCOUNT_RATE_IN_USE.csv"), decision_ref="90")
    reg.add("finance_wacc_mode", "Decision 90: research.finance.wacc_mode = uniform (main) | country_specific (implemented only, not run: new-build capital costs re-annualised with the country rate of COUNTRY_WACC_PUBLIC_SOURCES.csv; "
            "refuses to build while any country is DATA_PENDING - currently all 11, see wacc_country_model_*)", "uniform", "flag", "B", "S4C instruction S4C-0 item 3", f"{cfg} research.finance.wacc_mode", INSTRUCTION_SHA, decision_ref="90")
    for c_, r in sorted(solar24.items()):
        reg.add(f"wacc_iea_solar_2024_{c_}", f"{c_} utility-scale solar PV (50-100 MW) WACC, FID 2024, IEA Cost of Capital Observatory: {r['published_cell']} (nominal, post-tax, local currency"
                + (", indicative: limited responses" if r["indicative"] else "") + "); midpoint shown, range in the sensitivity columns; not used by the model (nominal basis)",
                (r["wacc_low"] + r["wacc_high"]) / 2, "per unit (nominal post-tax)", "B", "IEA Cost of Capital Observatory, Dashboard (2025 update)", f"{IEA_DASH_URL} (fetched {FETCHED_UTC}); table solar PV 50 MW or 100 MW",
                sha256(IEA_DASH), country=c_, sensitivity_low=r["wacc_low"], sensitivity_high=r["wacc_high"], decision_ref="90", status="REFERENCE_ONLY")
    for c_ in ASEAN:
        reg.add(f"wacc_country_model_{c_}", f"{c_} real WACC for wacc_mode country_specific: " + ("only nominal post-tax values published (IEA, see wacc_iea_*); real conversion not estimated" if c_ in solar24 else "no public country estimate found"),
                None, "per unit (real)", "C", "IEA Cost of Capital Observatory; IRENA 2023 (not retrievable)", "research_inputs/finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv", "", country=c_, decision_ref="90", status="DATA_PENDING")
    reg.add("wacc_irena_2023_not_retrievable", "IRENA (2023) The cost of financing for renewable power: PDF not retrievable on 2026-10-16 (irena.org HTTP 403 for the publication page and the media PDF; apren.pt mirror 404); not used",
            "not_retrieved", "flag", "B", "IRENA 2023", "https://www.irena.org/Publications/2023/May/The-cost-of-financing-for-renewable-power", INSTRUCTION_SHA, decision_ref="90", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4c_0.csv")
    print("wacc rows", len(rows), "registry rows", len(reg.rows), "solar 2024", {k: v["published_cell"] for k, v in solar24.items()})


if __name__ == "__main__":
    main()
