"""V5 X20 revision 1-4 (decision 241; Q15 (a)): MY ground-mounted solar land-use variants of research.demand.v5.solar_landuse_my
(research_inputs/renewable_v5/SOLAR_MY_LANDUSE_VARIANTS_V5.csv). The country increment is spread over the MY nodes in proportion to their
current caps (no raster recomputation, Q15 (a)), i.e. one factor on every MY ground-mounted solar candidate (v5_layers.apply_solar_cap_scale).

  base cap    = sum of the MY 'solar' candidate p_nom_max of the electric base x research.renewable.solar_density (5.1 / 4.6), = the build value
  oil_palm    = (base + FAOSTAT 2019-2023 mean harvested area of oil palm fruit (QCL item 254, registry_v5/sources) x 5.1 MW/km2) / base  (X03 section 4.4
                method: 51,700 km2, 86 -> 350 GW; grade C, the area is planted land, not eligibility-screened)
  open_forest = 198 / 86.4 (X20_SPEC.md 1.4 item 3, X03 section 4.5 [E]: LC100 classes 121-126 counted as eligible after the protected-area
                exclusion; grade C); cross-check column: raw LC100 121-126 area of MY (X03 cache lc100_country_class_area.csv) x 5.1 MW/km2, without the
                exclusion, reported only
    PYTHONHASHSEED=0 python scripts_project/v5_solar_my_variants_data.py --lc100 <X03 cache>/gwa_lc100/lc100_country_class_area.csv
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import netCDF4
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_inputs/renewable_v5/SOLAR_MY_LANDUSE_VARIANTS_V5.csv"
EB = ROOT / "results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc"
FAO = ROOT / "research_inputs/registry_v5/sources/FAOSTAT_QCL_ASEAN11_2019_2024.csv"
X03_OPEN_FOREST_GW = 198.0   # X03 REPORT.md section 4.5 item 3 [E]
OPEN_FOREST_CLASSES = (121, 122, 123, 124, 125, 126)


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--lc100", type=Path, required=True); ap.add_argument("--network", type=Path, default=EB); a = ap.parse_args(argv)
    sd = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())["research"]["renewable"]["solar_density"]
    dens = float(sd["target_mw_per_km2"]); built = float(sd["built_mw_per_km2"])
    ds = netCDF4.Dataset(a.network)
    car = np.array([str(x) for x in ds["generators_carrier"][:]]); ext = np.array(ds["generators_p_nom_extendable"][:]).astype(bool)
    bus = np.array([str(x) for x in ds["generators_bus"][:]]); pmax = np.array(ds["generators_p_nom_max"][:], dtype=float)
    bc = dict(zip([str(x) for x in ds["buses_i"][:]], [str(x) for x in ds["buses_country"][:]])); ds.close()
    sel = (car == "solar") & ext & np.array([bc.get(b) == "MY" for b in bus])
    base = float(pmax[sel].sum()) * dens / built
    fao = pd.read_csv(FAO)
    r = fao[(fao.ISO2 == "MY") & (fao["Item Code"] == 254) & (fao.Element == "Area harvested")]
    assert len(r) == 1 and r.Unit.iloc[0] == "ha"
    palm_km2 = float(r[[f"Y{y}" for y in range(2019, 2024)]].mean(axis=1).iloc[0]) / 100.0
    lc = pd.read_csv(a.lc100)
    of_km2 = float(lc[(lc.country == "MY") & lc.lc100_class.isin(OPEN_FOREST_CLASSES)].area_km2.sum())
    rows = [dict(variant="lc100", factor=1.0, cap_before_mw=base, cap_after_mw=base, added_area_km2=0.0, density_mw_per_km2=dens, grade="B",
                 basis="v5 main: LC100 eligibility of the electric base (research.renewable.solar_density 5.1 MW/km2)", source="", source_sha256="", crosscheck_factor_raw_area=np.nan),
            dict(variant="open_forest", factor=X03_OPEN_FOREST_GW * 1e3 / (86.4e3), cap_before_mw=base, cap_after_mw=base * X03_OPEN_FOREST_GW / 86.4, added_area_km2=np.nan, density_mw_per_km2=dens,
                 grade="C", basis="X20_SPEC 1.4 item 3 / X03 section 4.5 [E]: LC100 121-126 counted as eligible after the protected-area exclusion, MY 86.4 -> 198 GW",
                 source=str(a.lc100.name), source_sha256=sha(a.lc100), crosscheck_factor_raw_area=(base + of_km2 * dens) / base),
            dict(variant="oil_palm", factor=(base + palm_km2 * dens) / base, cap_before_mw=base, cap_after_mw=base + palm_km2 * dens, added_area_km2=palm_km2, density_mw_per_km2=dens,
                 grade="C", basis="X03 section 4.4 method: FAOSTAT QCL 2019-2023 mean harvested area of oil palm fruit (item 254) x 5.1 MW/km2 added to the MY cap, spread pro rata",
                 source=str(FAO.relative_to(ROOT)), source_sha256=sha(FAO), crosscheck_factor_raw_area=np.nan)]
    t = pd.DataFrame(rows)
    t.to_csv(OUT, index=False, lineterminator="\n")   # full float precision (the build reads the factor from this file)
    print(f"MY base cap {base:,.2f} MW (electric base x {dens}/{built}); oil palm {palm_km2:,.2f} km2; LC100 121-126 raw {of_km2:,.2f} km2")
    print(t[["variant", "factor", "cap_after_mw", "crosscheck_factor_raw_area"]].to_string(index=False))


if __name__ == "__main__":
    main()
