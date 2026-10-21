"""M08b B2 (M08-6; decisions 126, 133): temperature-band split of the 'other industry' bucket from JRC-IDEES-2021 (grade C).

JRC-IDEES-2021 EU27 'Other industrial sectors' (sheet OIS_fec), final energy 2019 by process and carrier. Each process is mapped to a
useful-heat band (assumption, grade C; temperature levels from the DEA industrial process heat catalogue):
  low    (< 150 C):   low-enthalpy heat, thermal / steam drying, thermal / steam process cooling (absorption);
  medium (150-400 C): steam processing (DEA: industrial steam typically 8 bar / 175 C, steam boilers 125-300 C);
  high   (> 400 C):   thermal processing = fuel-fired process heating (DEA: direct firing 400-1,600 C);
  mechanical:         diesel motors (construction / mining machinery) - not heat, the fuel stays a final-energy demand.
Electric processes (lighting, motors, electric processing / drying / cooling, electric machinery) are not split: the other-bucket electricity
stays electricity (s3_0_industry.py). Distributed steam, solar / geothermal and ambient heat have no ASEAN carrier and are left out.
Output: per model carrier (coal, oil, gas, biomass) the shares of the four uses, written to INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv.

    python scripts_project/m08b_heat_bands.py      # M08B_IDEES_XLSX overrides the workbook path (ignored input)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from d1_common import DEMAND_DIR, SRC_DIR, sha256, write_json   # noqa: E402

SCRIPT = "scripts_project/m08b_heat_bands.py"
XLSX = Path(os.environ.get("M08B_IDEES_XLSX", SRC_DIR / "jrc_idees_2021" / "EU27" / "JRC-IDEES-2021_Industry_EU27.xlsx"))
OUT = DEMAND_DIR / "INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv"
EVIDENCE = DEMAND_DIR / "INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.json"
SHEET, YEAR = "OIS_fec", "2019"
USES = ["low", "medium", "high", "mechanical"]
PROCESS_USE = {
    "Low-enthalpy heat": "low",
    "Other Industrial sectors: Steam processing": "medium",
    "Other Industrial sectors: Thermal processing": "high",
    "Other Industries: Thermal drying": "low",
    "Other Industries: Steam drying": "low",
    "Other Industries: Thermal cooling": "low",
    "Other Industries: Steam cooling": "low",
    "Other Industrial sectors: Diesel motors (incl. biofuels)": "mechanical",
}
SINGLE_CARRIER = {"Other Industrial sectors: Diesel motors (incl. biofuels)": "oil"}   # process row without carrier sub-rows
CARRIER = {"Solids": "coal", "Derived gases": "coal", "Refinery gas": "oil", "LPG": "oil", "Diesel oil and liquid biofuels": "oil", "Fuel oil": "oil",
           "Other liquids": "oil", "Natural gas and biogas": "gas", "Biomass and waste": "biomass", "Electricity": "electricity",
           "Distributed steam": None, "Solar and geothermal": None, "Ambient heat": None}
FUELS = ["coal", "oil", "gas", "biomass"]


def read_ois(path: Path = XLSX) -> pd.DataFrame:
    """(process, jrc_carrier, model_carrier, use, ktoe) rows of the OIS final-energy split in YEAR."""
    d = pd.read_excel(path, SHEET, header=None)
    col = next(j for j, v in enumerate(d.iloc[0]) if str(v).split(".")[0] == YEAR)
    rows, proc = [], None
    for i in range(4, len(d)):
        lab = d.iat[i, 0]
        if not isinstance(lab, str) or not lab.strip():
            continue
        lab = lab.strip()
        if lab.startswith("Market shares"):
            break
        v = float(d.iat[i, col]) if pd.notna(d.iat[i, col]) else 0.0
        if lab in CARRIER:
            if proc is not None:
                rows.append(dict(process=proc, jrc_carrier=lab, model_carrier=CARRIER[lab], use=PROCESS_USE.get(proc, "electric_or_other"), ktoe=v))
            continue
        proc = lab
        if lab in SINGLE_CARRIER:
            rows.append(dict(process=lab, jrc_carrier="(process row)", model_carrier=SINGLE_CARRIER[lab], use=PROCESS_USE[lab], ktoe=v))
    return pd.DataFrame(rows)


def shares(df: pd.DataFrame) -> pd.DataFrame:
    f = df[df.model_carrier.isin(FUELS) & df.use.isin(USES)]
    t = f.pivot_table(index="model_carrier", columns="use", values="ktoe", aggfunc="sum").reindex(index=FUELS, columns=USES).fillna(0.0)
    out = t.div(t.sum(axis=1), axis=0)
    out.columns = [f"share_{u}" for u in USES]
    t.columns = [f"ktoe_{u}" for u in USES]
    return pd.concat([out, t], axis=1).reset_index().rename(columns={"model_carrier": "carrier"})


def main():
    df = read_ois()
    sh = shares(df)
    if not (abs(sh[[f"share_{u}" for u in USES]].sum(axis=1) - 1.0) < 1e-12).all():
        raise ValueError("band shares do not sum to 1")
    sh.to_csv(OUT, index=False, float_format="%.10g")
    el = df[df.model_carrier == "electricity"]
    write_json(dict(script=SCRIPT, source=dict(file="JRC-IDEES-2021_Industry_EU27.xlsx", sheet=SHEET, year=YEAR, sha256=sha256(XLSX)), process_use=PROCESS_USE,
                    carrier_map=CARRIER, grade="C", rows=df.to_dict(orient="records"),
                    electricity_note=dict(thermal_electricity_low_enthalpy_ktoe=float(el.ktoe.sum()),
                                          remark="only the low-enthalpy electricity row has a carrier split; electric processing / drying / cooling and machinery are separate process rows; "
                                                 "the ASEAN other-bucket electricity is kept as electricity (non-thermal) in s3_0_industry.py"),
                    excluded=["Distributed steam", "Solar and geothermal", "Ambient heat", "Other Industries: Thermal cooling (no carrier split in the sheet)"],
                    output=dict(file=OUT.name, sha256=sha256(OUT))), EVIDENCE)
    print(sh.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
