"""V3 (decisions 163, 163-appendix; D163-1 to D163-6): industry sub-sector structure inside the unchanged country totals.

    PYTHONHASHSEED=0 python scripts_project/v3_industry.py --chain-dir <scratch dir>

The AEO8 country x sector anchors and the v2 RAS result are not touched. Starting from the v2 table
INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv:
  * every country total is split into steel, cement, ammonia, dispersed (the energy-fallback sub-sectors of s3_0_industry.py) and other;
  * VN: the sub-sector split of s3_0_industry.py is re-run on the APEC 2022 matrix (scratch copy of the data chain; the production tables are not touched);
  * ID (nickel, primary aluminium, alumina, copper) and MY (primary aluminium): explicit non-ferrous metals from production x unit energy;
  * D163-6 a: Other_v3(c) = T_v2(c) - sum of the explicit sub-sectors, i.e. the bound total of every country stays at its v2 value and the residual stays in other.
Cases: main (2019 production, Wei 2020 nickel), nf2023 (2023 production), niupper (nickel upper bound). Nothing is solved.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

from d1_common import ASEAN, DEMAND_DIR, REG_DIR, ROOT, sha256

SCRIPT = "scripts_project/v3_industry.py"
V3_DIR = ROOT / "research_inputs/industry_v3"
SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
OUTPUT_RULE = DEMAND_DIR / "INDUSTRY_OUTPUT_2050_M08B.csv"
RATIOS = REG_DIR / "INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv"
CARRIERS = ("coal", "oil", "gas", "biomass", "electricity", "hydrogen", "heat", "ammonia", "methanol", "heat_medium_a", "heat_medium_b", "heat_high")
RATIO_TO_OUT = {"elec": "electricity", "coal": "coal", "coke": "coal", "biomass": "biomass", "methane": "gas", "hydrogen": "hydrogen", "heat": "heat", "ammonia": "ammonia", "methanol": "methanol"}   # = s3_0_industry.RATIO_TO_OUT
ELASTICITY = 0.5           # research.s2.industry.physical_output_elasticity (registry industry_output_elasticity)
USEFUL_HEAT_EFF = 0.90     # = s3_0_industry.HEAT_EFF, registry existing_boiler_efficiency
NI_UPPER_MWH_PER_T_NPI = 26.0   # review D163-2: reverse-engineered APEC 2022 / USGS upper bound, sensitivity only
NI_NPI_NI_FRACTION = 380000.0 / 3200000.0   # USGS 2023 Indonesia Table 1, 2019: Ni content / gross weight of NPI
CASES = ("main", "nf2023", "niupper")


def col(car: str) -> str:
    return "pe_biomass_before_overflow_mwh" if car == "biomass" else f"pe_{car}_mwh"


def future_vectors() -> dict:
    r = pd.read_csv(RATIOS, index_col=0)
    return {s: {oc: float(sum(r.at[k, s] for k, v in RATIO_TO_OUT.items() if v == oc)) for oc in CARRIERS if oc in RATIO_TO_OUT.values()} for s in r.columns}


def decompose(row: pd.Series, fut: dict) -> dict:
    """{sub-sector: {carrier: MWh}} of one country row; the five parts sum to the row by construction (dispersed = residual)."""
    total = {c: float(row[col(c)]) for c in CARRIERS}
    z = lambda: {c: 0.0 for c in CARRIERS}
    steel, cement, ammonia, other = z(), z(), z(), z()
    for oc in fut["Cement"]:
        steel[oc] = fut["DRI + Electric arc"][oc] * float(row.primary_dri_2050_t) + fut["Electric arc"][oc] * float(row.secondary_eaf_2050_t)
        cement[oc] = fut["Cement"][oc] * float(row.cement_2050_t)
    ammonia["ammonia"] = total["ammonia"]
    other["electricity"] = float(row.other_electricity_2050_mwh)
    for f in ("coal", "oil", "gas", "biomass"):
        other[f] = float(row[f"other_mechanical_{f}_mwh"])
    other["heat"] = float(row.other_heat_low_mwh)
    for b in ("medium_a", "medium_b", "high"):
        other[f"heat_{b}"] = float(row[f"other_heat_{b}_mwh"])
    disp = {c: total[c] - steel[c] - cement[c] - ammonia[c] - other[c] for c in CARRIERS}
    if disp["hydrogen"] < 0:   # chlorine by-product credit of the v2 route (s3_0_industry floors the country value at 0): net against the steel hydrogen
        steel["hydrogen"] += disp["hydrogen"]; disp["hydrogen"] = 0.0
    bad = {c: v for c, v in disp.items() if v < -1e-3 * max(1.0, total[c])}
    if bad:
        raise ValueError(f"{row.name}: negative dispersed part {bad}")
    return dict(steel=steel, cement=cement, ammonia=ammonia, dispersed={c: max(0.0, v) for c, v in disp.items()}, other=other)


def nickel_unit_energy() -> dict:
    """Final energy per t contained Ni from Wei et al. 2020 Table 8, Case 3-FeNi (RKEF): electricity + fuel (drying, kiln, reductant), mining excluded."""
    t = pd.read_csv(V3_DIR / "NICKEL_ENERGY_WEI2020.csv")
    ni = float(t.ni_fraction.iloc[0])
    el = t[t.counted_as == "electricity"]; fu = t[t.counted_as == "fuel"]
    el_mwh = float(el.quantity.sum()) / 1000.0 / ni
    fuel_mwh = float((fu.quantity * fu.lhv_mj_per_kg).sum()) / 3600.0 / ni
    return dict(electricity_mwh_per_t_ni=el_mwh, fuel_mwh_per_t_ni=fuel_mwh, useful_heat_mwh_per_t_ni=fuel_mwh * USEFUL_HEAT_EFF)


def nonferrous(fut: dict, case: str, ne: dict) -> dict:
    """{country: {sub-sector: {carrier: MWh}}}, 2050: production x growth rule x unit energy."""
    p = pd.read_csv(V3_DIR / "NONFERROUS_PRODUCTION_V3.csv"); rule = pd.read_csv(OUTPUT_RULE).set_index("country")
    base, qcol = (2023, "q_2023_t") if case == "nf2023" else (2019, "q_2019_t")
    scale_ni = 1.0
    if case == "niupper":
        scale_ni = (NI_UPPER_MWH_PER_T_NPI / NI_NPI_NI_FRACTION) / (ne["electricity_mwh_per_t_ni"] + ne["fuel_mwh_per_t_ni"])
    out, led = {}, {}
    for c, g in p.groupby("country"):
        G = float(rule.at[c, "gdp_growth_2022_2050"]); f = G ** ((2050 - base) / 28.0 * ELASTICITY)
        if base == 2019 and abs(f - float(rule.at[c, "ammonia_growth_factor"])) > 1e-9:
            raise ValueError(f"{c}: growth factor {f} differs from the v2 ammonia rule {rule.at[c, 'ammonia_growth_factor']}")
        d = {}
        for route, x in g.groupby("route"):
            q = float(x[qcol].sum()) * f
            v = {k: 0.0 for k in CARRIERS}
            if route == "nickel":
                v["electricity"] = q * ne["electricity_mwh_per_t_ni"] * scale_ni; v["heat_high"] = q * ne["useful_heat_mwh_per_t_ni"] * scale_ni
                key = "nonferrous_nickel"
            else:
                sec, key = {"aluminium_primary": ("Aluminium - primary production", "nonferrous_aluminium_primary"), "alumina": ("Alumina production", "nonferrous_alumina"),
                            "other_nonferrous": ("Other non-ferrous metals", "nonferrous_copper")}[route]
                for oc, e in fut[sec].items():
                    v[oc] = q * e
            d[key] = v
            led[f"{c}:{key}"] = dict(q_2050_t=q, growth_factor=f, base_year=base)
        out[c] = d
    return out, led


def run_vn_chain(chain: Path) -> pd.Series:
    """Scratch copy of the data chain with the VN sub-sector shares of the cache replaced by the APEC 2022 matrix; returns the VN row of the heat-band summary."""
    if chain.exists():
        shutil.rmtree(chain)
    chain.mkdir(parents=True)
    shutil.copytree(ROOT / "research_inputs", chain / "research_inputs")
    shutil.copytree(ROOT / "scripts_project", chain / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
    (chain / "scripts_project/retired").mkdir(exist_ok=True)
    cp = chain / "research_inputs/assembly_v1/sources/industry_cache.json"
    cache = json.loads(cp.read_text())
    a = pd.read_csv(V3_DIR / "APEC2022_VN_INDUSTRY_PJ.csv").set_index("cache_subsector")
    carmap = dict(coal="coal_pj", oil="oil_pj", gas="gas_pj", biomass="biomass_pj", electricity="electricity_pj")
    n = 0
    for r in cache["records"]:
        if r["country"] != "VN":
            continue
        k = carmap[r["carrier"]]
        for s in r:
            if s in ("country", "carrier"):
                continue
            r[s] = float(a.at[s, k]) if s in a.index else 0.0
        n += 1
    if n != len(carmap):
        raise ValueError(f"VN cache records {n}")
    cp.write_text(json.dumps(cache))
    r = subprocess.run([sys.executable, "s3_0_industry.py"], cwd=chain / "scripts_project", capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-2000:])
    a_ = pd.read_csv(chain / "research_inputs/demand_v5" / SUMMARY).set_index("country")
    b_ = pd.read_csv(DEMAND_DIR / SUMMARY).set_index("country")
    same = [c for c in a_.index if c != "VN" and all(abs(float(a_.at[c, col(x)]) - float(b_.at[c, col(x)])) <= 1e-6 * max(1.0, abs(float(b_.at[c, col(x)]))) for x in CARRIERS)]
    if len(same) != len(a_.index) - 1:
        raise ValueError(f"the scratch chain does not reproduce the other countries: {sorted(set(a_.index) - set(same) - {'VN'})}")
    return a_.loc["VN"]


def main():
    p = argparse.ArgumentParser(); p.add_argument("--chain-dir", type=Path, required=True); a = p.parse_args()
    v2 = pd.read_csv(DEMAND_DIR / SUMMARY).set_index("country"); fut = future_vectors(); ne = nickel_unit_energy()
    vn = run_vn_chain(a.chain_dir)
    rows, evid, tables = [], dict(script=SCRIPT, nickel_unit_energy=ne, cases={}), {}
    for case in CASES:
        nf, led = nonferrous(fut, case, ne)
        t = v2.copy(); check = {}
        for c in v2.index:
            T = float(sum(v2.at[c, col(x)] for x in CARRIERS))
            src = vn if c == "VN" else v2.loc[c]
            parts = decompose(src, fut)
            parts.update(nf.get(c, {}))
            expl = sum(sum(v.values()) for k, v in parts.items() if k != "other")
            s_other = sum(parts["other"].values())
            if T <= 0:
                continue
            f = (T - expl) / s_other if s_other > 0 else 1.0
            if f < 0:   # D163-4 a: scale the new explicit sub-sectors so that Other = 0
                raise ValueError(f"{c}: explicit sub-sectors exceed the country total (D163-4 case not expected, stop and report)")
            parts["other"] = {k: v * f for k, v in parts["other"].items()}
            for s, v in parts.items():
                for k, x in v.items():
                    if abs(x) > 0:
                        rows.append(dict(case=case, country=c, subsector=s, carrier=k, mwh_2050=x))
            for k in CARRIERS:
                x = sum(v[k] for v in parts.values())
                t.at[c, col(k)] = x
                if k == "biomass":
                    t.at[c, "pe_biomass_mwh"] = x
            for key in ("biomass_source_band_medium_a_share", "biomass_source_band_medium_b_share", "biomass_source_band_high_share"):
                t.at[c, key] = float(src[key])
            check[c] = dict(total_v2_mwh=T, total_v3_mwh=float(sum(sum(v.values()) for v in parts.values())), other_scale=f, other_share_v3=sum(parts["other"].values()) / T,
                            other_share_v2=sum(decompose(v2.loc[c], fut)["other"].values()) / T, explicit_new_mwh=float(sum(sum(v.values()) for k, v in parts.items() if k.startswith("nonferrous"))))
        for c, z in check.items():
            if abs(z["total_v3_mwh"] - z["total_v2_mwh"]) > 1e-9 * z["total_v2_mwh"]:
                raise ValueError(f"{c}: country total not conserved")
        tables[case] = t
        evid["cases"][case] = dict(by_country=check, nonferrous=led)
    V3_DIR.mkdir(parents=True, exist_ok=True)
    for case, t in tables.items():
        sfx = "" if case == "main" else f"_{case.upper()}"
        t.reset_index().to_csv(V3_DIR / f"INDUSTRY_2050_SUMMARY_V3{sfx}.csv", index=False)
    pd.DataFrame(rows).sort_values(["case", "country", "subsector", "carrier"]).to_csv(V3_DIR / "INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv", index=False)
    evid["inputs"] = {f.name: sha256(f) for f in sorted(V3_DIR.glob("*.csv")) if f.name.startswith(("APEC", "NICKEL", "NONFERROUS"))}
    (V3_DIR / "INDUSTRY_V3_EVIDENCE.json").write_text(json.dumps(evid, indent=1, sort_keys=True) + "\n")
    z = pd.DataFrame(evid["cases"]["main"]["by_country"]).T
    print((z.assign(total_twh=z.total_v3_mwh / 1e6, new_twh=z.explicit_new_mwh / 1e6)[["total_twh", "new_twh", "other_share_v2", "other_share_v3", "other_scale"]]).round(4).to_string())
    print("sum TWh", round(z.total_v3_mwh.sum() / 1e6, 3), "nickel unit energy", {k: round(v, 3) for k, v in ne.items()})


if __name__ == "__main__":
    main()
