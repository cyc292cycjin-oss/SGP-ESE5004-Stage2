"""S3-2 data layer: extra-ASEAN import prices (decisions 17/18/64).

Green carriers: base prices = Neumann et al. (arXiv:2404.03927; Nature Communications 2025, doi:10.1038/s41467-025-60652-1) import cost
results deposited on Zenodo (doi:10.5281/zenodo.14872184, results.parquet, CC-BY-4.0): scenario "default", year 2040 (the only year in the
dataset; the published text quotes these 2040 values, e.g. Fischer-Tropsch 125-132 EUR/MWh, hydrogen by pipeline 74-88 EUR/MWh), subcategory
"Cost per MWh delivered", minimum over exporters - the same reduction PyPSA-Eur's add_import_options applies (import branch commit 5a87cedd,
prepare_sector_network.py lines 4616-4620 and 4703-4708). Decision 17: +20 % markup for ASEAN; sensitivity switch +-20 % on the applied price.
Fossil imports: WEO 2025 2050 prices registered in D1 (LNG via terminals, S3-1; oil regional bus and coal per node, S3-2); scenario per
research.fuels.price_scenario (S4C-0, decision 85: STEPS main, NZE low-price sensitivity; the reference table lists the main scenario).

    python scripts_project/s3_2_imports_data.py
"""
from __future__ import annotations

import pandas as pd

from d1_common import REG_DIR, ROOT, SRC_DIR, Registry, sha256, write_csv, write_json
from s2_costs import FUEL_PRICE_IDS

MAIN_FUEL_SCENARIO = "steps"   # S4C-0 (decision 85): configs/research/baseline.yaml research.fuels.price_scenario (main)

SCRIPT = "scripts_project/s3_2_imports_data.py"
NEU = SRC_DIR / "neumann2024"
PARQUET = NEU / "zenodo_14872184_results.parquet"
ZENODO_URL = "https://zenodo.org/api/records/14872184/files/results.parquet/content"
ZENODO_DOI = "10.5281/zenodo.14872184"
FETCHED_UTC = "2026-10-15T16:18:42Z"
NATCOMMS_HTML_SHA = "1f47340de706c43fe36395b5482ece47343ae1c4dbe941ec66fbb02e6511d76c"   # https://www.nature.com/articles/s41467-025-60652-1 fetched 2026-10-15T16:16:45Z
ARXIV_SHA = "b6a9f1b38cb6f651adf2b01c2b6882a77bf502e904b03a505d92bb0b76471567"           # arXiv:2404.03927v1 PDF fetched 2026-10-15T10:05:48Z
PE_IMPORT_SHA = "cc1c9ec4284a319ab4daa7d4916b268f4d8cba9c28396e0b17dc52269f7d4392"      # PyPSA-Eur 5a87cedd prepare_sector_network.py fetched 2026-10-15T16:15:27Z
OUT = ROOT / "research_inputs/imports_v5"
MARKUP = 0.20          # decision 17
SENSITIVITY = 0.20     # +-20 % switch (research.s3.imports.price_sensitivity)
CARRIERS = {   # esc in the Zenodo results -> model carrier
    "shipping-lh2": dict(carrier="hydrogen", bus="node H2 at LNG terminal nodes", paper="hydrogen by ship (liquid H2); published text: ship 18 % above the cheapest pipeline supplier (74-88 EUR/MWh)"),
    "shipping-lnh3": dict(carrier="ammonia", bus="ASEAN ammonia (regional)", paper="ammonia by ship; published text: hydrogen derivatives from Argentina/Chile, cheapest exporters within 10 %"),
    "shipping-meoh": dict(carrier="methanol", bus="ASEAN methanol (regional)", paper="methanol by ship; published text: methanol slightly cheaper than Fischer-Tropsch (20 % vs 50 % minimum part load)"),
    "shipping-ftfuel": dict(carrier="oil non-fossil", bus="ASEAN oil non-fossil (regional)", paper="Fischer-Tropsch fuel by ship; published text 125-132 EUR/MWh (Argentina/Chile)"),
}
REFERENCE_ONLY = {"pipeline-h2": "hydrogen by pipeline (no overland exporter route to ASEAN in scope; reference)", "shipping-lch4": "methane by ship (green LNG; ASEAN LNG is priced with the WEO fossil LNG price, S3-1; reference)",
                  "hvdc-to-elec": "electricity by HVDC (not an S3 import option; reference)"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pq_sha = sha256(PARQUET)
    df = pd.read_parquet(PARQUET).reset_index()
    sel = df[(df.subcategory == "Cost per MWh delivered") & (df.scenario == "default")]
    years = sorted(str(y) for y in sel.year.unique()); assert years == ["2040"], years   # the deposited dataset holds the 2040 assumptions only
    best = sel.loc[sel.groupby("esc").value.idxmin()].set_index("esc")
    rows = []
    for esc, meta in {**CARRIERS, **{k: dict(carrier="reference", bus="", paper=v) for k, v in REFERENCE_ONLY.items()}}.items():
        b = best.loc[esc]; base = float(b.value)
        applied = base * (1 + MARKUP)
        rows.append(dict(esc=esc, carrier=meta["carrier"], model_bus=meta["bus"], base_eur2020_per_mwh=round(base, 4), cheapest_exporter=b.exporter, delivered_to=b.importer, year=b.year, scenario=b.scenario,
                         markup=MARKUP, applied_eur2020_per_mwh=round(applied, 4), sensitivity_low=round(applied * (1 - SENSITIVITY), 4), sensitivity_high=round(applied * (1 + SENSITIVITY), 4),
                         n_exporters=int((sel.esc == esc).sum()), within_10pct_of_min=int(((sel.esc == esc) & (sel.value <= base * 1.10)).sum()),
                         status="REGISTERED" if meta["carrier"] != "reference" else "REFERENCE_ONLY", paper_note=meta["paper"],
                         source=f"Zenodo {ZENODO_DOI} results.parquet (scenario default, year 2040, Cost per MWh delivered, min over exporters as PyPSA-Eur add_import_options lines 4616-4620/4703-4708)"))
    write_csv(rows, OUT / "IMPORT_PRICES_2050.csv", list(rows[0].keys()))
    # fossil references (D1 registry)
    reg_df = pd.read_csv(REG_DIR / "fragments" / "fuel_prices.csv", dtype=str, keep_default_na=False).set_index("param_id")
    ids = {c: FUEL_PRICE_IDS[MAIN_FUEL_SCENARIO].format(c=c) for c in ("gas", "oil", "coal")}; scen = ids["gas"].split("_")[3]
    fossil = [dict(carrier=c, price_eur2020_per_mwh=(float(reg_df.loc[pid, "value"]) if pid else None), registry_id=pid, model_bus=bus, note=note) for c, pid, bus, note in [
        ("gas (LNG)", ids["gas"], "node gas via LNG terminals (S3-1)", f"WEO 2025 {scen} 2050 Japan LNG (S4C-0 main, decision 85); regasification adder DATA_PENDING"),
        ("oil", ids["oil"], "ASEAN oil (regional, S3-2)", f"WEO 2025 {scen} 2050 crude import price (S4C-0 main); one regional pool (decision 18), per-node pools removed"),
        ("coal", ids["coal"], "node coal (per node, unchanged S2 structure)", f"WEO 2025 {scen} 2050 steam coal Japan (S4C-0 main); per-node unlimited supply kept (decision 18)"),
        ("lignite", "", "node lignite (per node)", "S2 structure kept; cost-layer lignite fuel row (technology-data v0.15.0); WEO Table 2.3 has no lignite price (S3 table listed the coal NZE id here, which the build never applied)")]]
    write_csv(fossil, OUT / "IMPORT_PRICES_FOSSIL_2050.csv", list(fossil[0].keys()))
    # registry
    reg = Registry(SCRIPT)
    src = "Neumann et al. 2025 Nat. Commun. (doi:10.1038/s41467-025-60652-1) results dataset, Zenodo " + ZENODO_DOI
    loc = f"results.parquet fetched read-only {FETCHED_UTC} from {ZENODO_URL}; published text (nature.com, fetched 2026-10-15T16:16:45Z): Fischer-Tropsch 125-132, hydrogen pipeline 74-88 EUR/MWh; arXiv v1 p.12/p.15: FT reference 109.8 (2050 assumptions)"
    for r in rows:
        cid = r["carrier"].replace(" ", "_").replace("-", "_")
        if r["status"] == "REGISTERED":
            reg.add(f"import_price_base_{cid}", f"{r['esc']}: base import cost delivered to Europe, 2040 assumptions, cheapest exporter {r['cheapest_exporter']} ({r['n_exporters']} exporter rows, {r['within_10pct_of_min']} within +10 %); {r['paper_note']}",
                    r["base_eur2020_per_mwh"], "EUR2020/MWh", "B", src, loc, f"parquet:{pq_sha}|natcomms_html:{NATCOMMS_HTML_SHA}|arxiv:{ARXIV_SHA}", decision_ref="17")
            reg.add(f"import_price_{cid}", f"{r['esc']}: applied ASEAN import price = base x 1.20 (decision 17); same in both scenarios; imports only; sensitivity switch +-20 %",
                    r["applied_eur2020_per_mwh"], "EUR2020/MWh", "B", src + " x decision 17 markup", loc, f"parquet:{pq_sha}", decision_ref="17", sensitivity_low=r["sensitivity_low"], sensitivity_high=r["sensitivity_high"])
        else:
            reg.add(f"import_price_reference_{r['esc'].replace('-', '_')}", f"{r['esc']}: {r['paper_note']}; base {r['base_eur2020_per_mwh']} EUR/MWh (cheapest exporter {r['cheapest_exporter']})", r["base_eur2020_per_mwh"], "EUR2020/MWh", "B", src, loc,
                    f"parquet:{pq_sha}", decision_ref="17", status="REFERENCE_ONLY")
    reg.add("import_price_markup", "Markup on the Neumann et al. European delivered import costs for ASEAN (decision 17)", MARKUP, "fraction", "B", "S3 instruction S3-2.2 / decision 17", "config research.s3.imports.markup", pq_sha, decision_ref="17")
    reg.add("import_price_sensitivity", "Import price sensitivity switch (research.s3.imports.price_sensitivity: -0.2 / 0 / +0.2 applied to the marked-up price)", SENSITIVITY, "fraction", "B", "S3 instruction S3-2.2", "config", pq_sha, decision_ref="17", status="SENSITIVITY")
    reg.add("import_price_representativeness", "The dataset gives costs delivered to European entry points (importers EUSW/EUS/EUSE/EUE and ports) from 60+ exporting regions; the cheapest exporters (EH Western Sahara, CL Chile, AR Argentina) are far from both Europe and ASEAN; "
            "shipping cost is a minor share and ten regions lie within +10 % of the minimum (published text, Supplementary Fig. 9), so the European minimum x 1.20 is used as the ASEAN proxy (INFERENCE; no ASEAN-specific supply curve in the paper)",
            "european_minimum_x_1.20", "method", "C", src, "published text + Supplementary Fig. 7-9", pq_sha, decision_ref="17", sensitivity_low=None, sensitivity_high=None, status="REFERENCE_ONLY")
    reg.add("import_carbon_treatment", "Imported green carriers carry zero carbon in the importing country (decision 64): no CO2 port on the import generators; PyPSA-Eur import branch (5a87cedd) books the exporter DAC credit as a negative atmosphere port on the import link "
            "(co2_intensity dict lines 4553-4557, efficiency2 = -CO2 intensity lines 4659-4665 and 4711-4717) and the combustion emission at the consumer, net zero in the importing region; the S3 origin-neutral non-fossil buses give the same net result without a credit",
            "zero_carbon_at_import", "method", "B", "PyPSA-Eur import branch commit 5a87cedd scripts/prepare_sector_network.py add_import_options", "lines 4502-4720", PE_IMPORT_SHA, decision_ref="64")
    reg.add("import_h2_terminal_rule", "Hydrogen (liquid) ship imports enter the node H2 bus at the LNG terminal nodes: p_nom_max = LNG terminal capacity (existing x 2.5, or proposed) as PyPSA-Eur maps shipping-lh2 to LNG entry points (translate dict line ~4540) with "
            "capacity_boost (config line 710); terminal capital cost 7018 x 1.2 EUR/MW/a (lines 4560-4563); nodes without LNG capacity get no H2 import", "lng_terminal_nodes", "method", "B",
            "PyPSA-Eur import branch commit 5a87cedd", "add_import_options", PE_IMPORT_SHA, decision_ref="17")
    reg.add("import_coal_structure", "Coal and lignite keep the S2 per-node pools with unlimited one-way supply (decision 18: not network-constrained) at the WEO price of research.fuels.price_scenario (coal; S4C-0 main STEPS) and the cost-layer lignite row; emissions booked at the consuming link in the consuming country", "per_node", "method", "B",
            "S3 instruction S3-2.1", "s3_layers.add_imports", pq_sha, decision_ref="18")
    reg.add("import_oil_structure", "Oil: one regional pool bus ASEAN oil with the external import generator (WEO crude price of research.fuels.price_scenario; S4C-0 main STEPS); node oil buses connect to the pool through free bidirectional distribution links (decision 18), per-node external oil removed; FT/BtL outputs stay on the node buses until S3-5",
            "regional_pool", "method", "B", "S3 instruction S3-2.1", "s3_layers.add_imports", pq_sha, decision_ref="18")
    reg.write(REG_DIR / "fragments" / "imports.csv")
    write_json(dict(script=SCRIPT, sources=dict(parquet=pq_sha, zenodo_doi=ZENODO_DOI, zenodo_url=ZENODO_URL, fetched_utc=FETCHED_UTC, natcomms_html=NATCOMMS_HTML_SHA, arxiv_v1=ARXIV_SHA, pypsa_eur_import_branch=PE_IMPORT_SHA,
                    zenodo_config=sha256(NEU / "zenodo_14872184_config.20240826-z1.yaml")), rows=rows, fossil=fossil, markup=MARKUP, sensitivity=SENSITIVITY), OUT / "IMPORT_PRICES_EVIDENCE.json")
    pd.set_option("display.width", 250)
    print(pd.DataFrame(rows)[["esc", "carrier", "base_eur2020_per_mwh", "cheapest_exporter", "applied_eur2020_per_mwh", "within_10pct_of_min", "status"]].to_string())


if __name__ == "__main__":
    main()
