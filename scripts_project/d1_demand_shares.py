"""D1 section 4 (decision 21): exogenous demand-side technology shares from PyPSA-Eur v2025.07.0.

Values are read from config/config.default.yaml of the tagged release (copied to
research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml) and registered as
grade C assumptions with a sensitivity range taken from the same trajectory (2040 and 2050
values) or, for binary shares, the full [0, 1] interval. Items that do not apply to ASEAN
(space heating, district heating, retrofitting) are listed as REFERENCE_ONLY (decision 25:
cooling stays inside the electricity load; no heating sector).
"""
from __future__ import annotations

import yaml

from d1_common import REG_DIR, SRC_DIR, Registry, src_sha, write_json

SCRIPT = "scripts_project/d1_demand_shares.py"
CFG = "pypsa_eur_v2025.07.0_config.default.yaml"
SRC = "PyPSA-Eur v2025.07.0 config/config.default.yaml (https://github.com/PyPSA/pypsa-eur/blob/v2025.07.0/config/config.default.yaml)"

# (section, key, description, applies_to_asean, decision_ref)
TRAJECTORIES = [
    ("sector", "land_transport_electric_share", "Share of land transport final energy service met by battery-electric vehicles", True, "21"),
    ("sector", "land_transport_fuel_cell_share", "Share of land transport met by hydrogen fuel-cell vehicles", True, "21"),
    ("sector", "land_transport_ice_share", "Share of land transport met by internal combustion engines (oil)", True, "21"),
    ("sector", "shipping_hydrogen_share", "Share of shipping energy met by hydrogen", True, "21 (S3)"),
    ("sector", "shipping_methanol_share", "Share of shipping energy met by methanol", True, "21 (S3)"),
    ("sector", "shipping_oil_share", "Share of shipping energy met by oil", True, "21 (S3)"),
    ("sector", "reduce_space_heat_exogenously_factor", "Exogenous space-heat demand reduction (retrofitting)", False, "25"),
    ("industry", "St_primary_fraction", "Primary (ore-based) steel fraction", True, "21"),
    ("industry", "DRI_fraction", "Fraction of primary steel via hydrogen direct reduction (DRI + EAF)", True, "21"),
    ("industry", "Al_primary_fraction", "Primary aluminium fraction", True, "21"),
    ("industry", "HVC_primary_fraction", "Primary (virgin) high-value chemicals fraction", True, "21"),
    ("industry", "HVC_mechanical_recycling_fraction", "HVC mechanical recycling fraction", True, "21"),
    ("industry", "HVC_chemical_recycling_fraction", "HVC chemical recycling fraction", True, "21"),
]
SCALARS = [
    ("sector", "transport_electric_efficiency", "BEV efficiency: 1 MWh_el = 53.19 x 100 km", True, "21"),
    ("sector", "transport_fuel_cell_efficiency", "FCEV efficiency: 1 MWh_H2 = 30.003 x 100 km", True, "21"),
    ("sector", "transport_ice_efficiency", "ICE efficiency: 1 MWh_oil = 16.0712 x 100 km", True, "21"),
    ("sector", "aviation_demand_factor", "Aviation demand multiplier (1 = exogenous demand as projected)", True, "21,10"),
    ("sector", "HVC_demand_factor", "High-value chemicals demand multiplier", True, "21"),
    ("sector", "agriculture_machinery_electric_share", "Agriculture machinery electric share", True, "21"),
    ("sector", "agriculture_machinery_oil_share", "Agriculture machinery oil share", True, "21"),
    ("sector", "agriculture_machinery_fuel_efficiency", "Agriculture machinery fuel efficiency", True, "21"),
    ("sector", "agriculture_machinery_electric_efficiency", "Agriculture machinery electric efficiency", True, "21"),
    ("sector", "bev_dsm", "BEV demand-side management enabled", True, "21"),
    ("sector", "bev_dsm_availability", "Share of BEVs available for DSM", True, "21"),
    ("sector", "bev_energy", "BEV battery energy (MWh per vehicle)", True, "21"),
    ("sector", "bev_charge_efficiency", "BEV charging efficiency", True, "21"),
    ("sector", "bev_charge_rate", "BEV charge rate (MW per vehicle)", True, "21"),
    ("sector", "bev_avail_max", "Maximum share of BEVs plugged in", True, "21"),
    ("sector", "bev_avail_mean", "Mean share of BEVs plugged in", True, "21"),
    ("sector", "bev_dsm_restriction_value", "BEV DSM restriction value (state of charge)", True, "21"),
    ("sector", "bev_dsm_restriction_time", "BEV DSM restriction hour", True, "21"),
    ("sector", "shipping_hydrogen_liquefaction", "Shipping hydrogen liquefaction flag", True, "21 (S3)"),
    ("sector", "MWh_MeOH_per_MWh_H2", "Methanolisation: MWh methanol per MWh hydrogen", True, "21 (S3)"),
    ("sector", "MWh_MeOH_per_tCO2", "Methanolisation: MWh methanol per tCO2", True, "21 (S3)"),
    ("sector", "MWh_MeOH_per_MWh_e", "Methanolisation: MWh methanol per MWh electricity", True, "21 (S3)"),
    ("industry", "HVC_environment_sequestration_fraction", "HVC fraction sequestered in the environment (plastics not burned)", True, "21,S2 feedstock"),
    ("industry", "waste_to_energy", "Waste-to-energy of non-recycled plastics enabled", True, "21,S2 feedstock"),
    ("industry", "waste_to_energy_cc", "Waste-to-energy with carbon capture", True, "21,S2 feedstock"),
    ("sector", "ammonia", "Ammonia modelled explicitly", True, "21 (S3)"),
    ("industry", "MWh_NH3_per_tNH3", "Ammonia LHV MWh per tonne", True, "21 (S3)"),
    ("industry", "MWh_H2_per_tNH3_electrolysis", "Hydrogen input per tonne ammonia (Haber-Bosch)", True, "21 (S3)"),
    ("industry", "MWh_elec_per_tNH3_electrolysis", "Electricity input per tonne ammonia (Haber-Bosch)", True, "21 (S3)"),
    ("industry", "MWh_elec_per_tHVC_mechanical_recycling", "Electricity per tonne HVC mechanical recycling", True, "21"),
    ("industry", "MWh_elec_per_tHVC_chemical_recycling", "Electricity per tonne HVC chemical recycling", True, "21"),
    ("sector", "reduce_space_heat_exogenously", "Space heat reduction switch", False, "25"),
]
NESTED = [
    ("sector", ("district_heating", "progress"), "District heating progress (share of potential realised)", False, "25"),
]


def line_numbers(text: str):
    """key -> first line number where `  key:` (2-space indent) or `    year:` appears after it."""
    lines = text.splitlines()
    idx = {}
    for i, ln in enumerate(lines, 1):
        s = ln.split("#")[0].rstrip()
        if s.startswith("  ") and not s.startswith("   ") and ":" in s:
            idx.setdefault(s.strip().split(":")[0], i)
    return idx, lines


def year_line(lines, start, year):
    for j in range(start, min(start + 12, len(lines))):
        if lines[j].strip().startswith(f"{year}:"):
            return j + 1
    return None


def main():
    path = SRC_DIR / CFG
    text = path.read_text(encoding="utf-8")
    cfg = yaml.safe_load(text)
    sha = src_sha(CFG)
    idx, lines = line_numbers(text)
    reg = Registry(SCRIPT)
    out = []
    for section, key, desc, applies, dref in TRAJECTORIES:
        traj = cfg[section][key]
        v2050 = traj[2050]
        vals = [float(v) for y, v in traj.items() if int(y) >= 2040]
        ln = idx.get(key)
        ln2050 = year_line(lines, ln, 2050) if ln else None
        status = "REGISTERED" if applies else "REFERENCE_ONLY"
        lo, hi = (0.0, 1.0) if set(float(v) for v in traj.values()) <= {0.0, 1.0} else (min(vals), max(vals))
        reg.add(f"share_{key}_2050", desc + (" [not applicable to ASEAN: no heating sector, decision 25]" if not applies else "")
                + f"; trajectory {dict((int(y), float(v)) for y, v in traj.items())}", float(v2050), "fraction", "C", SRC,
                f"{section}: {key}: line {ln}, 2050 value line {ln2050}", sha, sensitivity_low=lo, sensitivity_high=hi,
                decision_ref=dref, status=status)
        out.append(dict(section=section, key=key, value_2050=v2050, line=ln, line_2050=ln2050, applies_to_asean=applies,
                        trajectory={int(y): float(v) for y, v in traj.items()}))
    for section, key, desc, applies, dref in SCALARS:
        v = cfg[section][key]
        ln = idx.get(key)
        status = "REGISTERED" if applies else "REFERENCE_ONLY"
        unit = "flag" if isinstance(v, bool) else ("fraction" if "share" in key or "fraction" in key or "avail" in key or "efficiency" in key and v <= 1 else "as in config")
        reg.add(f"share_{key}", desc + ("" if applies else " [not applicable to ASEAN, decision 25]"), v if not isinstance(v, bool) else str(v).lower(),
                unit, "C", SRC, f"{section}: {key}: line {ln}", sha,
                sensitivity_low=None if isinstance(v, bool) or not isinstance(v, (int, float)) else float(v) * 0.8,
                sensitivity_high=None if isinstance(v, bool) or not isinstance(v, (int, float)) else float(v) * 1.2,
                decision_ref=dref, status=status)
        out.append(dict(section=section, key=key, value=v, line=ln, applies_to_asean=applies))
    for section, keys, desc, applies, dref in NESTED:
        node = cfg[section]
        for k in keys:
            node = node[k]
        v2050 = node[2050]
        ln = idx.get(keys[0])
        reg.add(f"share_{'_'.join(keys)}_2050", desc + " [not applicable to ASEAN, decision 25]", float(v2050), "fraction", "C", SRC,
                f"{section}: {'/'.join(keys)}: line {ln}", sha, sensitivity_low=0.0, sensitivity_high=1.0, decision_ref=dref,
                status="REFERENCE_ONLY")
        out.append(dict(section=section, key="/".join(keys), value_2050=v2050, line=ln, applies_to_asean=applies))
    reg.add("share_source_version", "PyPSA-Eur release used for all exogenous demand-side shares", "v2025.07.0", "tag", "A", SRC,
            "git tag v2025.07.0", sha, decision_ref="21")
    reg.write(REG_DIR / "fragments" / "demand_shares.csv")
    write_json(dict(script=SCRIPT, config_sha256=sha, items=out), REG_DIR / "fragments" / "demand_shares.json")
    for o in out:
        print(o["section"], o["key"], o.get("value_2050", o.get("value")), "line", o["line"], "" if o["applies_to_asean"] else "[N/A ASEAN]")


if __name__ == "__main__":
    main()
