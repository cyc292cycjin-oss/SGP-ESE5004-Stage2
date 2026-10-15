"""S3-0.1 (decision 61): reproduce the PyPSA-Eur v2025.07.0 industry sector ratios from JRC-IDEES-2021 (EU27).

Runs the unmodified functions of scripts/build_industry_sector_ratios.py (local copy in registry_v5/sources, SHA
registered) on raw8/JRC-IDEES-2021_EU27.zip -> JRC-IDEES-2021_Industry_EU27.xlsx with the PyPSA-Eur
config.default.yaml industry parameters (reference_year 2019). Output: the 27-column future (best-in-class) sector
ratio table in MWh/t (and tCO2/t for process emissions) = the 2050 table of build_industry_sector_ratios_intermediate
(sector_ratios_fraction_future 2050 = 1.0, config line ~888). In addition the "today" (2019) specific energy of each
sector (sector total final energy / physical output from the same IDEES rows) is extracted so that the energy-based
fallback for ASEAN sub-sectors without physical activity can apply the implied 2019 -> 2050 efficiency change.

    python scripts_project/s3_0_industry_ratios.py
"""
from __future__ import annotations

import importlib.util
import re
import sys
import types
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from d1_common import REG_DIR, ROOT, SRC_DIR, Registry, sha256, src_sha, write_csv, write_json

SCRIPT = "scripts_project/s3_0_industry_ratios.py"
PE_SCRIPT = SRC_DIR / "pypsa_eur_v2025.07.0_build_industry_sector_ratios.py"
PE_CONFIG = SRC_DIR / "pypsa_eur_v2025.07.0_config.default.yaml"
IDEES_DIR = SRC_DIR / "jrc_idees_2021"
IDEES_XLSX = IDEES_DIR / "EU27" / "JRC-IDEES-2021_Industry_EU27.xlsx"
OUT_DIR = REG_DIR
# PyPSA-Eur v2025.07.0 config.default.yaml industry: block (lines 815-910); values copied verbatim with their line numbers
PE_INDUSTRY = dict(St_primary_fraction=0.3, DRI_fraction=1.0, H2_DRI=1.7, elec_DRI=0.322, Al_primary_fraction=0.2, MWh_NH3_per_tNH3=5.166, MWh_CH4_per_tNH3_SMR=10.8,
                   MWh_elec_per_tNH3_SMR=0.7, MWh_H2_per_tNH3_electrolysis=5.93, MWh_elec_per_tNH3_electrolysis=0.2473, MWh_NH3_per_MWh_H2_cracker=1.46,
                   NH3_process_emissions=24.5, petrochemical_process_emissions=25.5, HVC_primary_fraction=0.4, HVC_mechanical_recycling_fraction=0.30,
                   HVC_chemical_recycling_fraction=0.20, HVC_environment_sequestration_fraction=0.0, sector_ratios_fraction_future=1.0,
                   basic_chemicals_without_NH3_production_today=69.0, HVC_production_today=52.0, MWh_elec_per_tHVC_mechanical_recycling=0.547,
                   MWh_elec_per_tHVC_chemical_recycling=6.9, chlorine_production_today=9.58, MWh_elec_per_tCl=3.6, MWh_H2_per_tCl=-0.9372,
                   methanol_production_today=1.5, MWh_elec_per_tMeOH=0.167, MWh_CH4_per_tMeOH=10.25, MWh_MeOH_per_tMeOH=5.528, reference_year=2019,
                   oil_refining_emissions=0.013)
PE_CONFIG_LINES = dict(St_primary_fraction="823-830", DRI_fraction="831-838", H2_DRI="839", elec_DRI="840", Al_primary_fraction="841-848", MWh_NH3_per_tNH3="849",
                       MWh_CH4_per_tNH3_SMR="850", MWh_elec_per_tNH3_SMR="851", MWh_H2_per_tNH3_electrolysis="852", MWh_elec_per_tNH3_electrolysis="853",
                       NH3_process_emissions="855", petrochemical_process_emissions="856", sector_ratios_fraction_future="888-895", HVC_production_today="897",
                       MWh_elec_per_tHVC_mechanical_recycling="898", MWh_elec_per_tHVC_chemical_recycling="899", chlorine_production_today="900", MWh_elec_per_tCl="901",
                       MWh_H2_per_tCl="902", methanol_production_today="903", MWh_elec_per_tMeOH="904", MWh_CH4_per_tMeOH="905", MWh_MeOH_per_tMeOH="906", reference_year="908")
# EU27 ammonia production used by chemicals_industry() (script lines 431-436) to remove today's ammonia energy from the HVC ratio.
# PyPSA-Eur builds resources/ammonia_production.csv from the USGS Minerals Yearbook nitrogen table T12 (rule retrieve_usgs_ammonia_production,
# retrieve.smk lines 299-305; rule build_ammonia_production, build_sector.smk lines 743-758; scripts/build_ammonia_production.py). The USGS workbook
# and the PyPSA-Eur script were fetched read-only (S3-0, public data) and the resource is reproduced with the same code (sheet T12, skiprows 5,
# skipfooter 7, '--' = NaN, ktN x 17/14).
USGS_DIR = SRC_DIR / "pypsa_eur_data"
USGS_XLSX = USGS_DIR / "usgs_myb1-2022-nitro-ert.xlsx"
USGS_URL = "https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/files/myb1-2022-nitro-ert.xlsx"
USGS_FETCHED_UTC = "2026-10-15T10:30:38Z"
PE_AMMONIA_SCRIPT = USGS_DIR / "pypsa_eur_v2025.07.0_build_ammonia_production.py"
PE_AMMONIA_SCRIPT_URL = "https://raw.githubusercontent.com/PyPSA/pypsa-eur/v2025.07.0/scripts/build_ammonia_production.py"
PE_RETRIEVE_SMK = USGS_DIR / "pypsa_eur_v2025.07.0_retrieve.smk"
PE_BUILD_SECTOR_SMK = USGS_DIR / "pypsa_eur_v2025.07.0_build_sector.smk"
PE_FILES_FETCHED_UTC = "2026-10-15T10:29:53Z"
EU27 = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]


def build_ammonia_production(out_csv):
    """Reproduce PyPSA-Eur resources/ammonia_production.csv (ktNH3/a per country, 2018-2022) from the USGS workbook (same code as
    scripts/build_ammonia_production.py v2025.07.0)."""
    import country_converter as coco
    ammonia = pd.read_excel(USGS_XLSX, sheet_name="T12", skiprows=5, header=0, index_col=0, skipfooter=7, na_values=["--"])
    raw_index = list(ammonia.index)
    ammonia.index = coco.CountryConverter().convert(ammonia.index, to="iso2")
    years = [str(i) for i in range(2018, 2023)]
    ammonia = ammonia.rename(columns=lambda x: str(x))[years] * 17 / 14
    ammonia.index.name = "ktonNH3/a"
    ammonia.to_csv(out_csv)
    return ammonia, dict(zip(raw_index, list(ammonia.index)))
AMMONIA_FLAG = True   # config.default.yaml sector: ammonia: true (line 734) -> ammonia kept as its own carrier in the ratios


@contextmanager
def _mute():
    yield


def load_pe_module():
    """Import the PyPSA-Eur script with stubbed scripts._helpers and a mocked snakemake object."""
    helpers = types.ModuleType("scripts._helpers")
    helpers.configure_logging = lambda *a, **k: None
    helpers.set_scenario_config = lambda *a, **k: None
    helpers.mute_print = _mute
    scripts_pkg = types.ModuleType("scripts"); scripts_pkg.__path__ = []
    sys.modules["scripts"] = scripts_pkg; sys.modules["scripts._helpers"] = helpers
    spec = importlib.util.spec_from_file_location("pe_industry_sector_ratios", PE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    amm = OUT_DIR / "sources" / "jrc_idees_2021" / "ammonia_production.csv"   # PyPSA-Eur resource reproduced from USGS T12 (build_ammonia_production)
    build_ammonia_production(amm)
    mod.snakemake = types.SimpleNamespace(input=types.SimpleNamespace(idees=str(IDEES_DIR), ammonia_production=str(amm)),
                                          params=types.SimpleNamespace(industry=PE_INDUSTRY, ammonia=AMMONIA_FLAG), output=types.SimpleNamespace(industry_sector_ratios=None))
    spec.loader.exec_module(mod)
    mod.params = PE_INDUSTRY; mod.year = PE_INDUSTRY["reference_year"]
    return mod


def today_specific_energy(mod, src_text, eu27_ammonia_kt):
    """2019 EU27 specific final energy (MWh/t, all carriers) of each sector from the same IDEES rows the script uses:
    the first row of each `s_fec = idees["fec"][a:b]` slice is the sector total; the output is the `s_out` row."""
    rows = {}
    func_re = re.compile(r"^def (\w+)\(\):", re.M)
    funcs = [(m.group(1), m.start()) for m in func_re.finditer(src_text)]
    for i, (name, start) in enumerate(funcs):
        end = funcs[i + 1][1] if i + 1 < len(funcs) else len(src_text)
        body = src_text[start:end]
        m = re.search(r'sector = "([^"]+)"\s*\n\s*idees = load_idees_data\(sector\)', body)
        if not m:
            continue
        idees = mod.load_idees_data(m.group(1))
        # walk the sector blocks in order: sector = "X"; first fec slice; the s_out slice that follows
        blocks = list(re.finditer(r'(?<![A-Za-z_])sector = "([^"]+)"', body))   # not 'subsector = "..."'
        for i_b, bm in enumerate(blocks):
            sec = bm.group(1); text = body[bm.end():(blocks[i_b + 1].start() if i_b + 1 < len(blocks) else len(body))]
            fec = re.search(r'idees\["fec"\]\[(\d+):(\d+)\]', text); out = re.search(r'idees\["out"\]\[(\d+):(\d+)\]', text)
            hvc = re.search(r's_out = params\["HVC_production_today"\] \* 1e3', text)
            if not fec or not (out or hvc):
                continue
            a, b = int(fec.group(1)), int(fec.group(2))
            s_fec = idees["fec"][a:b]
            if str(s_fec.index[0]) != sec:
                continue   # derived columns (DRI + Electric arc, recycling, Ammonia, Chlorine, Methanol) have no own IDEES total row
            total_ktoe = float(s_fec.iloc[0])
            if out:
                o = int(out.group(1)); s_out = idees["out"][o:o + 1]; out_kt = float(s_out.iloc[0]); out_label = str(s_out.index[0]); out_slice = f"{o}:{o + 1}"
            else:
                out_kt = PE_INDUSTRY["HVC_production_today"] * 1e3; out_label = "params HVC_production_today x 1e3 (kt)"; out_slice = "params"
            feed = feed_ng = 0.0; today_mwh_per_t = None
            if sec == "Basic chemicals":
                # Feedstock block (script lines 328-345): naphtha-type rows -> naphtha (excluded here: feedstock, R2), 'Natural gas' -> methane (PyPSA-Eur
                # counts the feedstock natural gas as methane energy; the 2019 value below follows the same convention so that the 2050/2019 factor is
                # consistent: basic-chemicals energy use + feedstock natural gas - today's ammonia (SMR), chlorine and methanol energy (lines 431-448), per t HVC).
                s_feed = idees["fec"][14:23]
                assert str(s_feed.index[0]).startswith("Chemicals: Feedstock")
                feed = float(s_feed.iloc[0]); feed_ng = float(s_feed["Natural gas"])
                nh3 = eu27_ammonia_kt * 1e3 * (PE_INDUSTRY["MWh_CH4_per_tNH3_SMR"] + PE_INDUSTRY["MWh_elec_per_tNH3_SMR"])
                cl = PE_INDUSTRY["chlorine_production_today"] * 1e6 * (PE_INDUSTRY["MWh_elec_per_tCl"] + PE_INDUSTRY["MWh_H2_per_tCl"])
                meoh = PE_INDUSTRY["methanol_production_today"] * 1e6 * (PE_INDUSTRY["MWh_CH4_per_tMeOH"] + PE_INDUSTRY["MWh_elec_per_tMeOH"])
                today_mwh_per_t = ((total_ktoe - feed + feed_ng) * mod.toe_to_MWh * 1e3 - nh3 - cl - meoh) / (PE_INDUSTRY["HVC_production_today"] * 1e6)
            key = "HVC" if sec == "Basic chemicals" else sec
            rows[key] = dict(sector=key, fec_2019_ktoe=total_ktoe, feedstock_2019_ktoe=feed, feedstock_natural_gas_2019_ktoe=feed_ng, output_2019_kt=out_kt, output_label=out_label,
                             today_total_mwh_per_t=(today_mwh_per_t if today_mwh_per_t is not None else (((total_ktoe - feed) * mod.toe_to_MWh / out_kt) if out_kt else None)),
                             fec_row=str(s_fec.index[0]), fec_slice=f"{a}:{b}", out_slice=out_slice)
    return rows


def main():
    src_text = PE_SCRIPT.read_text()
    mod = load_pe_module()
    parts = [mod.iron_and_steel(), mod.chemicals_industry(), mod.nonmetalic_mineral_products(), mod.pulp_paper_printing(), mod.food_beverages_tobacco(),
             mod.non_ferrous_metals(), mod.transport_equipment(), mod.machinery_equipment(), mod.textiles_and_leather(), mod.wood_and_wood_products(), mod.other_industrial_sectors()]
    df = pd.concat(parts, axis=1); df.index.name = "MWh/tMaterial"
    df.to_csv(OUT_DIR / "INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv")
    amm_csv = OUT_DIR / "sources" / "jrc_idees_2021" / "ammonia_production.csv"
    amm_df = pd.read_csv(amm_csv, index_col=0)
    eu27_listed = sorted(set(amm_df.index.intersection(EU27))); eu27_amm = float(amm_df.loc[eu27_listed, "2019"].sum())
    today = today_specific_energy(mod, src_text, eu27_amm)
    future_total = df.loc[["elec", "coal", "coke", "biomass", "methane", "hydrogen", "heat", "ammonia", "methanol"]].sum()   # naphtha (feedstock) excluded: energy use only
    trows = []
    for sec in df.columns:
        t = today.get(sec)
        trows.append(dict(sector=sec, future_total_mwh_per_t=float(future_total[sec]), today_total_mwh_per_t=(t["today_total_mwh_per_t"] if t else None),
                          efficiency_factor_2050_over_2019=((float(future_total[sec]) / t["today_total_mwh_per_t"]) if (t and t["today_total_mwh_per_t"]) else None),
                          fec_2019_ktoe=(t["fec_2019_ktoe"] if t else None), feedstock_2019_ktoe=(t.get("feedstock_2019_ktoe", 0.0) if t else None),
                          feedstock_natural_gas_2019_ktoe=(t.get("feedstock_natural_gas_2019_ktoe", 0.0) if t else None), output_2019_kt=(t["output_2019_kt"] if t else None), output_label=(t["output_label"] if t else ""),
                          today_source_rows=((f'fec[{t["fec_slice"]}] row "{t["fec_row"]}", out[{t["out_slice"]}]' + ("; energy use + feedstock natural gas (fec[14:23] Natural gas) - EU27 ammonia/chlorine/methanol energy (script lines 431-448), PyPSA-Eur convention" if sec == "HVC" else ""))
                                             if t else "no sector-total row (derived column, e.g. DRI + Electric arc / HVC recycling / Ammonia)")))
    tdf = pd.DataFrame(trows)
    write_csv(tdf.to_dict("records"), OUT_DIR / "INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv", list(tdf.columns))
    # function -> line numbers (for the report)
    func_lines = {m.group(1): src_text[:m.start()].count("\n") + 1 for m in re.finditer(r"^def (\w+)\(\):", src_text, re.M)}
    reg = Registry(SCRIPT)
    pe_sha, cfg_sha, x_sha = sha256(PE_SCRIPT), sha256(PE_CONFIG), sha256(IDEES_XLSX)
    reg.add("industry_sector_ratios_pypsa_eur_2050", "PyPSA-Eur v2025.07.0 industry sector ratios (27 sub-sectors, MWh/t incl. the low-temperature 'heat' row) reproduced from JRC-IDEES-2021 EU27 "
            "with the unmodified build_industry_sector_ratios.py functions; file INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", 27, "sectors", "B",
            "JRC-IDEES-2021 v1 EU27 Industry workbook (raw8, CC BY 4.0) x PyPSA-Eur v2025.07.0 scripts/build_industry_sector_ratios.py",
            "functions " + ", ".join(f"{k} (line {v})" for k, v in func_lines.items() if k not in ("load_idees_data",)), f"xlsx:{x_sha}|script:{pe_sha}|config:{cfg_sha}", decision_ref="61")
    reg.add("industry_sector_ratios_reference_year", "IDEES reference year used by the ratio script (config industry: reference_year)", PE_INDUSTRY["reference_year"], "year", "A",
            "PyPSA-Eur v2025.07.0 config.default.yaml", f"line {PE_CONFIG_LINES['reference_year']}", cfg_sha, decision_ref="61")
    usgs_sha, amm_script_sha, amm_csv_sha = sha256(USGS_XLSX), sha256(PE_AMMONIA_SCRIPT), sha256(amm_csv)
    reg.add("industry_sector_ratios_eu27_ammonia_2019", f"EU27 ammonia production 2019 subtracted from the HVC ratio (script lines 431-436): USGS Minerals Yearbook nitrogen table T12 (ktN x 17/14) "
            f"summed over the {len(eu27_listed)} EU27 producers listed ({', '.join(eu27_listed)}); PyPSA-Eur resources/ammonia_production.csv reproduced with scripts/build_ammonia_production.py; "
            f"USGS workbook fetched read-only {USGS_FETCHED_UTC} from {USGS_URL}", eu27_amm, "kt NH3/a", "B",
            "USGS Minerals Yearbook 2022 Nitrogen (myb1-2022-nitro-ert.xlsx) via PyPSA-Eur v2025.07.0 retrieve.smk lines 299-305 / build_sector.smk lines 743-758",
            "sheet T12, column 2019", f"usgs:{usgs_sha}|script:{amm_script_sha}|csv:{amm_csv_sha}", decision_ref="61")
    reg.add("industry_sector_ratios_ammonia_source_files", "Read-only fetched PyPSA-Eur v2025.07.0 files for the ammonia resource (retrieve.smk, build_sector.smk, build_ammonia_production.py) and the USGS workbook; URLs, UTC fetch times and SHA256 in INDUSTRY_SECTOR_RATIOS_EVIDENCE.json",
            4, "files", "A", "github.com/PyPSA/pypsa-eur tag v2025.07.0; USGS National Minerals Information Center", f"fetched {PE_FILES_FETCHED_UTC} / {USGS_FETCHED_UTC}",
            f"retrieve:{sha256(PE_RETRIEVE_SMK)}|build_sector:{sha256(PE_BUILD_SECTOR_SMK)}|script:{amm_script_sha}|usgs:{usgs_sha}", decision_ref="61", status="REFERENCE_ONLY")
    for k, v in PE_INDUSTRY.items():
        if k in ("reference_year",):
            continue
        reg.add(f"industry_pe_param_{k}", f"PyPSA-Eur industry parameter {k} used by build_industry_sector_ratios.py", v, "as in config", "C", "PyPSA-Eur v2025.07.0 config.default.yaml",
                f"line {PE_CONFIG_LINES.get(k, '815-910')}", cfg_sha, sensitivity_low=v * 0.8 if isinstance(v, float) and v > 0 else None, sensitivity_high=v * 1.2 if isinstance(v, float) and v > 0 else None, decision_ref="61",
                status="REFERENCE_ONLY")
    for r in trows:
        if r["efficiency_factor_2050_over_2019"] is not None:
            reg.add(f"industry_efficiency_factor_{re.sub(r'[^A-Za-z0-9]+', '_', r['sector']).strip('_')}", f"{r['sector']}: future best-in-class specific energy {r['future_total_mwh_per_t']:.4g} MWh/t over 2019 EU27 {r['today_total_mwh_per_t']:.4g} MWh/t ({r['today_source_rows']})",
                    r["efficiency_factor_2050_over_2019"], "ratio", "B", "JRC-IDEES-2021 EU27 x PyPSA-Eur ratio script", r["today_source_rows"], x_sha, decision_ref="61")
    reg.write(REG_DIR / "fragments" / "industry_sector_ratios.csv")
    write_json(dict(script=SCRIPT, sources=dict(idees_xlsx=x_sha, pe_script=pe_sha, pe_config=cfg_sha), function_lines=func_lines, parameters=PE_INDUSTRY,
                    eu27_ammonia_kt_2019=eu27_amm, eu27_ammonia_countries_listed=eu27_listed,
                    ammonia_production_by_country_2019_kt=amm_df["2019"].dropna().round(3).to_dict(),
                    read_only_fetches=[dict(file=str(USGS_XLSX.relative_to(ROOT)), url=USGS_URL, fetched_utc=USGS_FETCHED_UTC, sha256=usgs_sha),
                                       dict(file=str(PE_AMMONIA_SCRIPT.relative_to(ROOT)), url=PE_AMMONIA_SCRIPT_URL, fetched_utc="2026-10-15T10:29:18Z", sha256=amm_script_sha),
                                       dict(file=str(PE_RETRIEVE_SMK.relative_to(ROOT)), url="https://raw.githubusercontent.com/PyPSA/pypsa-eur/v2025.07.0/rules/retrieve.smk", fetched_utc=PE_FILES_FETCHED_UTC, sha256=sha256(PE_RETRIEVE_SMK)),
                                       dict(file=str(PE_BUILD_SECTOR_SMK.relative_to(ROOT)), url="https://raw.githubusercontent.com/PyPSA/pypsa-eur/v2025.07.0/rules/build_sector.smk", fetched_utc=PE_FILES_FETCHED_UTC, sha256=sha256(PE_BUILD_SECTOR_SMK))],
                    ratios=df.round(6).to_dict(), today=trows), OUT_DIR / "INDUSTRY_SECTOR_RATIOS_EVIDENCE.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(df.round(3).T.to_string())
    print(tdf[["sector", "future_total_mwh_per_t", "today_total_mwh_per_t", "efficiency_factor_2050_over_2019"]].round(3).to_string())


if __name__ == "__main__":
    main()
