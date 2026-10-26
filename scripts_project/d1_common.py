"""D1 (2026-10-15) shared helpers: data registry rows, hashing, unit constants.

Every numeric value registered by the d1_* scripts carries a tier (A direct
source, B reproducible derivation, C assumption with sensitivity range), a
source locator and the SHA256 of the source file. Nothing here builds or
solves a network.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTAKE = Path(os.environ.get("D1_INTAKE", "/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake"))
EXTRACTION = INTAKE / "extraction"
UPSTREAM = Path(os.environ.get("D1_UPSTREAM", "/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean"))
TECHNOLOGY_DATA_V0_13_2 = Path(os.environ.get(
    "D1_TECHNOLOGY_DATA",
    "/mnt/d/ResearchWorkspaces/ASEAN/research/00_source_provenance/official/technology-data"))
REG_DIR = ROOT / "research_inputs" / "registry_v5"
SRC_DIR = REG_DIR / "sources"
DEMAND_DIR = ROOT / "research_inputs" / "demand_v5"
BIOMASS_DIR = ROOT / "research_inputs" / "biomass_v5"
COST_DIR = ROOT / "research_inputs" / "cost_layers_v5"
LNG_DIR = ROOT / "research_inputs" / "lng_terminals_v5"
WORK_DIR = ROOT / "work" / "p1_step2_20261015"

ASEAN = ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN"]
ASEAN10 = [c for c in ASEAN if c != "TL"]  # AEO8 regional totals exclude Timor-Leste
# DFX F3 (DFX_RULES section 3; weak point 8): the non-energy-use oil accounts of the D1 demand table that are HVC (petrochemical) feedstock;
# share_HVC_primary_fraction_2050 applies to these only. Every other NonEnergy:* oil account (bitumen, lubricants, paraffin waxes, petroleum coke,
# gas oil, motor gasoline, fuel oil) and the coal / gas rows keep factor 1.0.
HVC_FEEDSTOCK_ACCOUNTS = ("NonEnergy:Naphtha", "NonEnergy:Ethane", "NonEnergy:Liquefied petroleum gas (LPG)", "NonEnergy:Natural gas liquids")
NEU_GAS_ACCOUNT = "NonEnergy:Natural gas (including LNG)"   # DFX F2.4: the NEU natural-gas account from which the ammonia feedstock gas is deducted
ISO3 = {"BN": "BRN", "KH": "KHM", "ID": "IDN", "LA": "LAO", "MY": "MYS", "MM": "MMR",
        "PH": "PHL", "SG": "SGP", "TH": "THA", "TL": "TLS", "VN": "VNM"}
ISO2_FROM_ISO3 = {v: k for k, v in ISO3.items()}
UNSD_NAMES = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID",
              "Lao People's Dem. Rep.": "LA", "Lao People's Democratic Republic": "LA",
              "Malaysia": "MY", "Myanmar": "MM", "Philippines": "PH", "Singapore": "SG",
              "Thailand": "TH", "Timor-Leste": "TL", "Viet Nam": "VN"}
GEM_NAMES = {"Brunei": "BN", "Cambodia": "KH", "Indonesia": "ID", "Laos": "LA", "Malaysia": "MY",
             "Myanmar": "MM", "Philippines": "PH", "Singapore": "SG", "Thailand": "TH",
             "Timor-Leste": "TL", "Vietnam": "VN"}
FAO_NAMES = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID",
             "Lao People's Democratic Republic": "LA", "Malaysia": "MY", "Myanmar": "MM",
             "Philippines": "PH", "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL",
             "Viet Nam": "VN"}

COLUMNS = ["param_id", "description", "value", "unit", "country", "node", "tier", "source",
           "source_locator", "source_sha256", "derivation_script", "sensitivity_low",
           "sensitivity_high", "decision_ref", "status"]
TIERS = {"A", "B", "C"}
STATUSES = {"REGISTERED", "DATA_PENDING", "CANDIDATE_ONLY", "SENSITIVITY", "SOURCE_ZERO",
            "REFERENCE_ONLY", "ZERO_BY_DECISION"}
# EA20 GDP deflator (ECB Data Portal MNA.A.N.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.IX.D.N, 2020 = 100), used by S2-0
EA20_DEFLATOR_FILE = ROOT / "research_inputs" / "prices" / "sources" / "ECB_EA20_GDP_DEFLATOR.csv"
EA20_DEFLATOR_SERIES = "MNA.A.N.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.IX.D.N"
EA20_DEFLATOR_URL = ("https://data-api.ecb.europa.eu/service/data/MNA/A.N.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.IX.D.N"
                     "?format=csvdata&startPeriod=1990&endPeriod=2025")


def ea20_deflator() -> dict:
    """year -> EA20 GDP deflator index (2020 = 100) from the ECB CSV pinned in research_inputs/prices."""
    out = {}
    for r in read_csv(EA20_DEFLATOR_FILE):
        if r.get("KEY") == EA20_DEFLATOR_SERIES and r.get("TIME_PERIOD", "").isdigit():
            out[int(r["TIME_PERIOD"])] = float(r["OBS_VALUE"])
    if 2020 not in out or 2025 not in out:
        raise ValueError("EA20 deflator series incomplete")
    return out


# M08-1 (decision 131): Eurostat HICP annual average rate of change as used by technology-data v0.15.0 itself
# (scripts/_helpers.py prepare_inflation_rate, line 220: row "European Economic Area ..." for EUR, "United States" for USD;
# adjust_for_inflation.get_factor: product of (1 + rate) over the years, missing years filled with the series mean).
TD_V015_SRC_DIR = COST_DIR / "sources" / "technology_data_v0.15.0"
HICP_TD_FILE = TD_V015_SRC_DIR / "prc_hicp_aind__custom_20097956_spreadsheet.xlsx"   # technology-data v0.15.0 inputs/ (tarball c4787c1d)
HICP_DOWNLOAD_FILE = ROOT / "research_inputs" / "prices" / "sources" / "EUROSTAT_PRC_HICP_AIND_DEFAULTVIEW_2016_2025.xlsx"   # user download (cross-check)
HICP_DOWNLOAD_ORIGINAL_NAME = "prc_hicp_aind$defaultview_spreadsheet.xlsx"
HICP_EEA_ROW = "European Economic Area (EEA18-1995, EEA28-2004, EEA30-2007, EEA31-2013, EEA30-2020)"
HICP_US_ROW = "United States"


def hicp_rates(path: Path = HICP_TD_FILE, row: str = HICP_EEA_ROW) -> dict:
    """year -> annual average rate of change / 100, read exactly as technology-data v0.15.0 prepare_inflation_rate
    (Sheet 1, header row 9, ':' and 'd' are missing). Columns that are not years (flag columns) must be empty for the row."""
    import pandas as pd
    s = pd.read_excel(path, sheet_name="Sheet 1", index_col=0, na_values=[":", "d"], header=8).loc[row].dropna()
    extra = [c for c in s.index if not str(c).isdigit()]
    if extra:
        raise ValueError(f"non-year columns with values in the HICP row {row!r}: {extra[:3]}")
    return {int(c): float(v) / 100.0 for c, v in s.items()}


def hicp_factor(rates: dict, ref_year: int, target_year: int) -> float:
    """technology-data v0.15.0 adjust_for_inflation.get_factor(rates, ref_year, target_year): converts a value in
    ref_year money to target_year money (product of 1 + rate, missing years filled with the series mean)."""
    ref_year, target_year = int(ref_year), int(target_year)
    if ref_year == target_year:
        return 1.0
    mean = sum(rates.values()) / len(rates)
    lo, hi = sorted((ref_year, target_year))
    f = 1.0
    for y in range(lo + 1, hi + 1):
        f *= 1.0 + rates.get(y, mean)
    return f if ref_year < target_year else 1.0 / f


def eurostat_download_rates(path: Path = HICP_DOWNLOAD_FILE, sheet: str = "Sheet 6", row: str = HICP_EEA_ROW) -> dict:
    """year -> annual average rate of change / 100 from the Eurostat prc_hicp_aind default-view download (Sheet 6 = rates;
    value / flag column pairs after the 'TIME' header row). Cross-check only."""
    import openpyxl
    ws = openpyxl.load_workbook(path, data_only=True)[sheet]   # not read_only: the file lacks sheet dimensions (read_only sees one row)
    rows = list(ws.iter_rows(values_only=True))
    hdr = next(r for r in rows if r and r[0] == "TIME")
    years = [int(c) for c in hdr[1:] if c not in (None, "")]
    r = next(r for r in rows if r and r[0] == row)
    return {y: float(v) / 100.0 for y, v in zip(years, r[1:][::2]) if v not in (None, ":")}

# --- Unit constants used across D1 (registered once by d1_registry.py) ---------------------
# param_id: (value, unit, description, source, locator, tier)
UNIT_CONSTANTS = {
    "conv_mwh_per_toe": (11.63, "MWh/toe",
        "1 tonne of oil equivalent = 41.868 GJ = 1e7 kcal_IT; 41.868/3.6 = 11.63 MWh "
        "(research-layer convention ASSEMBLY_V1_MTOE_CONVENTION_11P63_TWH)",
        "IEA/OECD definition of toe; UNSD Energy Statistics 2014 conversion note gives the "
        "alternative UNSD convention 1,000 TOE = 42.6216 TJ (+1.8%), not used",
        "UNSD 2014 05.pdf p.xxiii (calorie 4.1868 J); configs/research/baseline.yaml mtoe_method", "A"),
    "conv_mwh_per_mbtu": (0.29307107, "MWh/MBtu",
        "1 Btu_IT = 1055.05585 J (NIST SP 811 B.9: 1.055 056 E+03); 1e6 Btu = 1.05505585 GJ",
        "NIST Guide to the SI, Special Publication 811, Appendix B.9",
        "British thermal unit_IT -> joule", "A"),
    "conv_gj_per_t_coal_6000kcal": (25.1208, "GJ/t",
        "6,000 kcal/kg x 4.1868 kJ/kcal (kcal_IT) = 25.1208 GJ/t; WEO steam coal prices are "
        "quoted per tonne adjusted to 6,000 kcal/kg",
        "NIST SP 811 B.9 kilocalorie_IT = 4.1868E+03 J; WEO 2025 Table 2.3 note",
        "Table 2.3 footnote (coal 6 000 kcal/kg)", "A"),
    "conv_gas_gcv_to_ncv": (0.90, "NCV/GCV",
        "UNSD standard factor for natural gas reported in TJ on a GCV basis -> NCV; same factor "
        "as the frozen research-layer reconstruction (natural gas TJ GCV x 0.90)",
        "UNSD Energy Statistics 2014, Standard net calorific values",
        "05.pdf p.xxiv: Natural gas (original unit is TJ on a GCV basis) 0.90", "A"),
    "conv_gj_per_t_crude_ncv": (42.30, "GJ/t",
        "Conventional crude oil standard NCV (same as frozen factor 0.01175 TWh/kt)",
        "UNSD Energy Statistics 2014 Standard net calorific values; IPCC 2006 Vol.2 Ch.1 "
        "Table 1.2 default 42.3 (40.1-44.8)",
        "05.pdf p.xxiv; IPCC Table 1.2 row Crude Oil", "A"),
    "conv_gj_per_t_ngl_ncv": (44.20, "GJ/t",
        "Natural gas liquids standard NCV (frozen factor 0.01228 TWh/kt)",
        "UNSD Energy Statistics 2014 Standard net calorific values", "05.pdf p.xxiv", "A"),
    "conv_gj_per_t_hardcoal_ncv": (25.80, "GJ/t",
        "Hard coal standard NCV (frozen factor 0.007167 TWh/kt)",
        "UNSD Energy Statistics 2014 Standard net calorific values", "05.pdf p.xxiv", "A"),
    "conv_gj_per_t_browncoal_ncv": (14.00, "GJ/t",
        "Brown coal (UNSD aggregate incl. lignite and sub-bituminous) standard NCV "
        "(frozen factor 0.003889 TWh/kt)",
        "UNSD Energy Statistics 2014 Standard net calorific values", "05.pdf p.xxiv", "A"),
    "conv_gj_per_t_natural_gas_mass": (48.0, "GJ/t",
        "Natural gas (and LNG, which is natural gas by mass) default NCV 48.0 TJ/Gg, "
        "95% CI 46.5-50.4",
        "IPCC 2006 Guidelines Vol.2 Ch.1 Table 1.2", "Table 1.2 row Natural Gas", "A"),
    "conv_gj_per_t_msw_biomass_fraction": (11.6, "GJ/t",
        "Municipal wastes (biomass fraction) default NCV 11.6 TJ/Gg, 95% CI 6.8-18.0 "
        "(as received)",
        "IPCC 2006 Guidelines Vol.2 Ch.1 Table 1.2",
        "Table 1.2 row Municipal Wastes (biomass fraction)", "A"),
    "conv_gj_per_m3_wood_residues": (9.14, "GJ/m3",
        "Fuelwood, wood residues and by-products: 9.14 TJ per 1,000 m3 solid volume at "
        "20-30% moisture",
        "UNSD Energy Statistics 2014 Standard net calorific values", "05.pdf p.xxiii-xxiv", "A"),
    "conv_bbl_m3": (0.1589873, "m3/bbl", "Barrel (42 US gallons) = 0.158 987 3 m3",
        "NIST SP 811 Appendix B.9",
        "barrel [for petroleum, 42 gallons (U.S.)] -> cubic meter 1.589 873 E-01", "A"),
    "conv_btu_per_bbl_crude_gcv": (5.689e6, "Btu/bbl",
        "US EIA energy conversion calculators: 1 barrel of crude oil = 5,689,000 Btu "
        "(US production basis, gross calorific value as used by EIA); used only as the "
        "barrel-to-energy bridge for WEO oil prices",
        "US EIA, Energy Explained, Energy conversion calculators (accessed 2026-10-15)",
        "https://www.eia.gov/energyexplained/units-and-calculators/energy-conversion-calculators.php",
        "B"),
    "conv_oil_gcv_to_ncv": (0.95, "NCV/GCV",
        "IPCC default: NCV is about 5% lower than GCV for oil and coal, 10% for natural gas",
        "IPCC 2006 Guidelines Vol.2 Ch.1 Box 1.1",
        "Box 1.1 Conversion between gross and net calorific values", "A"),
    "fx_usd_to_eur_2020": (0.8772286325726557, "EUR/USD",
        "Annual mean of ECB euro reference rates for 2020 (366 daily values incl. "
        "carried-forward non-trading days) as computed by currency_converter 0.18.9, the same "
        "package and method as pypsa-asean scripts/process_cost_data."
        "get_yearly_currency_exchange_rate with TECH_DATA_REFERENCE_YEAR = 2020",
        "ECB euro foreign exchange reference rates (eurofxref-hist.zip bundled with "
        "currency_converter 0.18.9)",
        "pypsa-asean/scripts/process_cost_data.py:91,170-177; recomputed in d1_cost_layers.py", "B"),
    "fx_usd_to_eur_2024": (0.9244229745458087, "EUR/USD",
        "Annual mean of ECB euro reference rates for 2024, same method (alternative path: "
        "convert first, then deflate in EUR; not used for the main values)",
        "ECB euro foreign exchange reference rates via currency_converter 0.18.9",
        "recomputed in d1_cost_layers.py", "B"),
    "deflator_usd_2024_to_2020": (105.377 / 125.587, "USD2020/USD2024",
        "US GDP implicit price deflator (index 2017=100): 2020 = 105.377, 2024 = 125.587 "
        "(annual); WEO 2025 prices are in USD (MER, 2024)",
        "FRED series A191RD3A086NBEA (U.S. Bureau of Economic Analysis), last updated 2026-09-30",
        "https://fred.stlouisfed.org/graph/fredgraph.csv?id=A191RD3A086NBEA rows 2020-01-01, "
        "2024-01-01", "A"),
}
# Derived: USD2024 -> EUR2020 (deflate in USD, then convert at the 2020 ECB mean rate)
USD2024_TO_EUR2020 = (UNIT_CONSTANTS["deflator_usd_2024_to_2020"][0]
                      * UNIT_CONSTANTS["fx_usd_to_eur_2020"][0])


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt(x) -> str:
    """Stable decimal text for CSV cells (empty for None)."""
    if x is None or x == "":
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, int):
        return str(x)
    return format(float(x), ".12g")


class Registry:
    """Collects DATA_REGISTRY rows for one script and writes a fragment CSV."""

    def __init__(self, script: str):
        self.script = script
        self.rows: list[dict] = []

    def add(self, param_id, description, value, unit, tier, source, source_locator,
            source_sha256, country="", node="", sensitivity_low=None, sensitivity_high=None,
            decision_ref="", status="REGISTERED"):
        if tier not in TIERS:
            raise ValueError(f"bad tier {tier} for {param_id}")
        if status not in STATUSES:
            raise ValueError(f"bad status {status} for {param_id}")
        if status == "DATA_PENDING":
            value = "DATA_PENDING"
        if any(r["param_id"] == param_id for r in self.rows):
            raise ValueError(f"duplicate param_id {param_id}")
        self.rows.append({
            "param_id": param_id, "description": description, "value": fmt(value), "unit": unit,
            "country": country, "node": node, "tier": tier, "source": source,
            "source_locator": source_locator, "source_sha256": source_sha256,
            "derivation_script": self.script, "sensitivity_low": fmt(sensitivity_low),
            "sensitivity_high": fmt(sensitivity_high), "decision_ref": decision_ref,
            "status": status})

    def write(self, path: Path):
        write_csv(sorted(self.rows, key=lambda r: r["param_id"]), path, COLUMNS)
        return path


def write_csv(rows, path, columns):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: fmt(r.get(k)) for k in columns})
    return path


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_json(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False, default=str)
                    + "\n", encoding="utf-8")
    return path


def src_sha(name: str) -> str:
    """SHA256 of a file copied under research_inputs/registry_v5/sources."""
    return sha256(SRC_DIR / name)
