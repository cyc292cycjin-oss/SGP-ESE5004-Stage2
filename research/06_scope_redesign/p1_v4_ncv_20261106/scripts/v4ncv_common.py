"""V4 W11 (NCV audit) shared readers and constants.

Paths (WSL view), the UNdata export (the same 52 files the upstream reads), the upstream conversion dictionary and fuel lists parsed from
pypsa-asean scripts/_helpers.py with ast (no import), the UNSD 2019 standard NCV table, the IPCC 2006 Vol. 2 Ch. 1 Table 1.2 defaults (both read
from the PDF page text in extracted/ and checked against the hard-coded copies below by v4ncv_references.py), and the transaction normaliser used to
match UNdata transactions to UN Energy Balances flows.

Nothing here writes to the repository.
"""
from __future__ import annotations

import ast
import glob
import re
from pathlib import Path

import pandas as pd

WORK = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_ncv_20261106")
REPO = Path("/home/jin/wt_v4_ncv")
PYPSA_ASEAN = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean")
UNSD_DIR = PYPSA_ASEAN / "data/demand/unsd/data"
SRC = REPO / "research_inputs/assembly_v1/sources"
TJ_PER_TWH = 3600.0

ASEAN = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID", "Lao People's Dem. Rep.": "LA", "Malaysia": "MY", "Myanmar": "MM",
         "Philippines": "PH", "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "Viet Nam": "VN"}
ISO = list(ASEAN.values())

# UNSD Energy Balances 2019, "Standard net calorific values" (PDF p.27-28, printed xxvi-xxvii; identical in the 2014 edition 05.pdf p.2-3).
# TJ per thousand metric tons unless stated; natural gas: original unit TJ (GCV), factor 0.90 to NCV; fuelwood TJ per 10^3 m3.
UNSD_STD = {
    "Hard coal": 25.80, "Brown coal": 14.00, "Peat": 9.76, "Oil shale": 8.90, "Coal coke": 28.20, "Patent fuel": 20.70,
    "Brown coal briquettes": 20.70, "Coal tar": 28.00, "Other coal products": 20.00, "Peat products": 9.76,
    "Conventional crude oil": 42.30, "Natural gas liquids": 44.20, "Additives and Oxygenates": 30.00, "Other hydrocarbons": 36.00,
    "Feedstocks": 43.00, "Refinery gas": 49.50, "Ethane": 46.40, "Liquefied petroleum gas": 47.30, "Naphtha": 44.50,
    "Aviation gasoline": 44.30, "Motor gasoline": 44.30, "Gasoline-type jet fuel": 44.30, "Kerosene-type jet fuel": 44.10,
    "Other kerosene": 43.80, "Gas-diesel oil": 43.00, "Fuel oil": 40.40, "White spirit": 40.20, "Lubricants": 40.20,
    "Paraffin waxes": 40.20, "Petroleum coke": 32.50, "Bitumen": 40.20, "Other oil products": 40.20,
    "Natural gas (GCV TJ -> NCV TJ)": 0.90, "Fuelwood (TJ per 10^3 m3)": 9.14, "Bagasse": 7.72, "Biogasoline": 26.80,
    "Biodiesels": 36.80, "Bio jet kerosene": 40.00, "Other liquid biofuels": 27.40, "Charcoal": 29.50,
}
UNSD_FUELWOOD_GJ_PER_M3_TEXT = 9.135   # conversion-factor text, PDF p.26: 9.135 GJ/m3 at 20-30 % moisture

# IPCC 2006 Vol. 2 Ch. 1 Table 1.2 (PDF p.18-19, printed 1.18-1.19): default NCV, lower, upper (TJ/Gg).
IPCC = {
    "Crude Oil": (42.3, 40.1, 44.8), "Natural Gas Liquids": (44.2, 40.9, 46.9), "Motor Gasoline": (44.3, 42.5, 44.8),
    "Aviation Gasoline": (44.3, 42.5, 44.8), "Jet Gasoline": (44.3, 42.5, 44.8), "Jet Kerosene": (44.1, 42.0, 45.0),
    "Other Kerosene": (43.8, 42.4, 45.2), "Gas/Diesel Oil": (43.0, 41.4, 43.3), "Residual Fuel Oil": (40.4, 39.8, 41.7),
    "Liquefied Petroleum Gases": (47.3, 44.8, 52.2), "Ethane": (46.4, 44.9, 48.8), "Naphtha": (44.5, 41.8, 46.5),
    "Bitumen": (40.2, 33.5, 41.2), "Lubricants": (40.2, 33.5, 42.3), "Petroleum Coke": (32.5, 29.7, 41.9),
    "Refinery Gas": (49.5, 47.5, 50.6), "Paraffin Waxes": (40.2, 33.7, 48.2), "Anthracite": (26.7, 21.6, 32.2),
    "Coking Coal": (28.2, 24.0, 31.0), "Other Bituminous Coal": (25.8, 19.9, 30.5), "Sub-Bituminous Coal": (18.9, 11.5, 26.0),
    "Lignite": (11.9, 5.50, 21.6), "Oil Shale and Tar Sands": (8.9, 7.1, 11.1), "Brown Coal Briquettes": (20.7, 15.1, 32.0),
    "Patent Fuel": (20.7, 15.1, 32.0), "Coke Oven Coke and Lignite Coke": (28.2, 25.1, 30.2), "Gas Coke": (28.2, 25.1, 30.2),
    "Coal Tar": (28.0, 14.1, 55.0), "Natural Gas": (48.0, 46.5, 50.4), "Peat": (9.76, 7.80, 12.5), "Wood/Wood Waste": (15.6, 7.90, 31.0),
    "Sulphite lyes (black liquor)": (11.8, 5.90, 23.0), "Other Primary Solid Biomass": (11.6, 5.90, 23.0), "Charcoal": (29.5, 14.9, 58.0),
    "Biogasoline": (27.0, 13.6, 54.0), "Biodiesels": (27.0, 13.6, 54.0), "Other Liquid Biofuels": (27.4, 13.8, 54.0),
}

# UNdata commodity (as spelled in the export) -> (UNSD standard key, IPCC key, coal parent group or None)
COMMODITY_REF = {
    "Hard coal": ("Hard coal", None, "hard"), "Hrad coal": ("Hard coal", None, "hard"),
    "Anthracite": ("Hard coal", "Anthracite", "hard_child"), "Other bituminous coal": ("Hard coal", "Other Bituminous Coal", "hard_child"),
    "Coking coal": ("Hard coal", "Coking Coal", "hard_child"),
    "Brown coal": ("Brown coal", None, "brown"), "Lignite": ("Brown coal", "Lignite", "brown_child"),
    "Sub-bituminous coal": ("Brown coal", "Sub-Bituminous Coal", "brown_child"),
    "Coke-oven coke": ("Coal coke", "Coke Oven Coke and Lignite Coke", None), "Coke oven coke": ("Coal coke", "Coke Oven Coke and Lignite Coke", None),
    "Coke Oven Coke": ("Coal coke", "Coke Oven Coke and Lignite Coke", None),
    "Brown coal briquettes": ("Brown coal briquettes", "Brown Coal Briquettes", None),
    "Brown Coal Briquettes": ("Brown coal briquettes", "Brown Coal Briquettes", None),
    "Patent fuel": ("Patent fuel", "Patent Fuel", None), "Peat": ("Peat", "Peat", None),
    "Gas Oil/ Diesel Oil": ("Gas-diesel oil", "Gas/Diesel Oil", None), "Motor Gasoline": ("Motor gasoline", "Motor Gasoline", None),
    "Motor gasoline": ("Motor gasoline", "Motor Gasoline", None),
    "Kerosene-type Jet Fuel": ("Kerosene-type jet fuel", "Jet Kerosene", None), "Aviation gasoline": ("Aviation gasoline", "Aviation Gasoline", None),
    "Gasoline-type jet fuel": ("Gasoline-type jet fuel", "Jet Gasoline", None), "Other kerosene": ("Other kerosene", "Other Kerosene", None),
    "Fuel oil": ("Fuel oil", "Residual Fuel Oil", None), "Liquefied petroleum gas (LPG)": ("Liquefied petroleum gas", "Liquefied Petroleum Gases", None),
    "Liquified Petroleum Gas (LPG)": ("Liquefied petroleum gas", "Liquefied Petroleum Gases", None),
    "Naphtha": ("Naphtha", "Naphtha", None), "Bitumen": ("Bitumen", "Bitumen", None), "Lubricants": ("Lubricants", "Lubricants", None),
    "Petroleum coke": ("Petroleum coke", "Petroleum Coke", None), "Petroleum Coke": ("Petroleum coke", "Petroleum Coke", None),
    "Paraffin waxes": ("Paraffin waxes", "Paraffin Waxes", None), "Refinery gas": ("Refinery gas", "Refinery Gas", None),
    "Refinery Gas": ("Refinery gas", "Refinery Gas", None), "Ethane": ("Ethane", "Ethane", None),
    "Natural gas liquids": ("Natural gas liquids", "Natural Gas Liquids", None),
    "Conventional crude oil": ("Conventional crude oil", "Crude Oil", None), "Crude petroleum": ("Conventional crude oil", "Crude Oil", None),
    "Additives and Oxygenates": ("Additives and Oxygenates", None, None),
    "Fuelwood": ("Fuelwood (TJ per 10^3 m3)", "Wood/Wood Waste", None), "Charcoal": ("Charcoal", "Charcoal", None),
    "Bagasse": ("Bagasse", "Other Primary Solid Biomass", None), "Biodiesel": ("Biodiesels", "Biodiesels", None),
    "Biogasoline": ("Biogasoline", "Biogasoline", None), "Bio jet kerosene": ("Bio jet kerosene", None, None),
}


def unsd_export() -> pd.DataFrame:
    """All UNdata export rows of the 11 ASEAN countries (all years), with commodity / transaction split as the upstream does."""
    fs = sorted(glob.glob(str(UNSD_DIR / "*.txt")))
    df = pd.concat((pd.read_csv(f, sep=";", dtype=str, keep_default_na=False).assign(SourceFile=Path(f).name,
                    PhysicalLine=lambda x: x.index + 2) for f in fs), ignore_index=True)
    df = df[df["Country or Area"].isin(ASEAN)].copy()
    sp = df["Commodity - Transaction"].str.split(" - ", n=1, expand=True)
    df["commodity"] = sp[0].str.strip()
    df["transaction"] = sp[1].fillna("").str.strip()
    df["country"] = df["Country or Area"].map(ASEAN)
    df["q"] = pd.to_numeric(df["Quantity"], errors="coerce")
    return df


def upstream_dicts() -> tuple[dict, dict]:
    """(fuels_conv_toTWh, fuel lists) from pypsa-asean scripts/_helpers.py, parsed with ast (no import)."""
    tree = ast.parse((PYPSA_ASEAN / "scripts/_helpers.py").read_text())
    conv, lists = None, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "get_conv_factors":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Assign) and isinstance(sub.value, ast.Dict) and len(sub.value.keys) > 10:
                    conv = ast.literal_eval(sub.value)
        if isinstance(node, ast.FunctionDef) and node.name == "aggregate_fuels":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Assign) and isinstance(sub.value, ast.List):
                    lists[sub.targets[0].id] = ast.literal_eval(sub.value)
    if conv is None or len(lists) != 6:
        raise ValueError("upstream dictionaries not found")
    return conv, lists


_FLOW_RULES = [
    (r"^final energy consumption$", "Finalenergyconsumption"),
    (r"^final consumption$", "Finalconsumption"),
    (r"^consumption by manufacturing, construction and non-fuel( mining)?( industry)?$", "Manufacturing,const.,mining"),
    (r"^consumption by other manuf\., const\. and non-fuel ind\.$", "OTHER_MANUF_AGG"),
    (r"^consumption by iron and steel( industry)?$", "Ironandsteel"),
    (r"^consumption by chemical( and petrochemical)?( ?industry)?$", "Chemicalandpetrochemical"),
    (r"^consumption by non-ferrous metals( industry)?$", "Non-ferrousmetals"),
    (r"^consumption by non-metallic minerals( industry)?$", "Non-metallicminerals"),
    (r"^consumption by transport equipment( industry)?$", "Transportequipment"),
    (r"^consumption by machinery( industry)?$", "Machinery"),
    (r"^consumption by mining and quarrying( industry)?$", "Miningandquarrying"),
    (r"^consumption by food(, beverage)? and tobacco( industry)?$", "Foodandtobacco"),
    (r"^consumption by paper, pulp and print(ing)?( industry)?$", "Paper,pulpandprinting"),
    (r"^consumption by wood and wood products( industry)?$", "Woodandwoodproducts"),
    (r"^consumption by textile and leather( industry)?$", "Textileandleather"),
    (r"^consumption by construction( industry)?$", "Construction"),
    (r"^consumption not elsewhere specified \(industry\)$|^consumption by industries not elsewhere specified$", "Industriesn.e.s"),
    (r"^consumption by households$", "Households"),
    (r"^consumption by commerce and public services$", "Commerce,publicservices"),
    (r"^consumption (in|by) agriculture, forestry and fishing$", "Agriculture,forestry,fishing"),
    (r"^consumption not elsewhere specified \(other\)$|^consumption by other consumers not elsewhere specified$", "Otherconsumers"),
    (r"^consumption by other$", "Other"),
    (r"^consumption by road$|^consumption in road$|^road$", "Road"),
    (r"^consumption by rail$|^consumption in rail$", "Rail"),
    (r"^consumption by domestic aviation$|^consumption in domestic aviation$", "Domesticaviation"),
    (r"^consumption by domestic navigation$|^consumption in domestic navigation$", "Domesticnavigation"),
    (r"^consumption by transport$|^consumption in transport$", "Transport"),
    (r"^consumption for non-energy uses?$|^non-energy uses?$", "Non-energyuse"),
    (r"^production$", "Primaryproduction"),
    (r"^imports$", "Imports"),
    (r"^exports$", "Exports"),
    (r"^transformation in electricity plants - main activity producers$|^transformation in main activity( producer)? electricity plants$",
     "Electricityplants_main"),
    (r"^transformation in electricity plants - autoproducers$|^transformation in autoproducer electricity plants$", "Electricityplants_auto"),
    (r"^transformation in electricity, chp and heat plants$", "ElectricityCHPHeat"),
]


def flow_of(transaction: str) -> str | None:
    t = re.sub(r"\s+", " ", transaction.strip().lower())
    for pat, flow in _FLOW_RULES:
        if re.match(pat, t):
            return flow
    return None
