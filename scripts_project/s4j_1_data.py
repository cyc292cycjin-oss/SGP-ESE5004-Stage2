"""S4J-1 data (decision 104, S4I K1): non-industrial electricity base load from the demand-table sectors.

  * NONINDUSTRIAL_ELECTRICITY_S4J1.csv: per country the demand-table 2050 electricity of the sectors in the base load (s2_layers.TABLE_BASE_SECTORS:
    residential, commercial, agriculture and others, transport), their 2019 base, the multiple, the Astar 2050 total (shape source), the base load of
    the former method (astar_residual build) and of the new one (table_sectors build, read back from the network), and the S4I A5 scheme (b) column
    (residential + commercial + agriculture and others) for comparison; ASEAN total row.
  * EXPLICIT_ELECTRICITY_INVENTORY_S4J1.csv: the electricity uses modelled separately (not in the base load), with the code location.
  * registry fragment s4j_1.

    python scripts_project/s4j_1_data.py --main <table_sectors build> --former <astar_residual build>
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv
from s2_layers import TABLE_BASE_SECTORS

SCRIPT = "scripts_project/s4j_1_data.py"
INSTRUCTION_SHA = "c20957448c69128c05eaf4e271bcca7f98eecc7ccd3121cd37f3581daff3348f"
LOC = "work/p1_step4j_20261018/S4J_CLAUDE_CODE_INSTRUCTION.md"
DEMAND = ROOT / "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"
A5 = ROOT / "research/06_scope_redesign/p1_step4i_20261018/evidence/followups/A5_astar_residual.csv"
OUT = ROOT / "research_inputs/demand_v5/NONINDUSTRIAL_ELECTRICITY_S4J1.csv"
INV = ROOT / "research_inputs/demand_v5/EXPLICIT_ELECTRICITY_INVENTORY_S4J1.csv"
INVENTORY = [   # electricity uses represented by their own load or link (never in the base load); code locations in scripts_project/s2_layers.py add_demand_layer
    ("Industry", "UNSD_electricity_Industry row", "replaced by the 2050 process-route electricity (IndustryElectricityRoutes load, incl. ammonia / methanol conversion "
     "electricity in convert_to_h2_and_gas mode) when research.s2.industry.carrier_mode = pypsa_eur_2050 (main); in bas_fixed it joins the base load",
     "industry block ('industry electricity demand')", "explicit"),
    ("Transport", "land-transport fuel rows (RoadResidualFuel, TransportNEC, TransportEmbeddedFuelParent)", "EV load on the EV battery bus (BEV charger) = fuel x EV share x "
     "ICE/EV efficiency ratio; FCEV hydrogen likewise - converts the NON-electric rows only", "transport block ('land transport EV')", "explicit (not the electricity row)"),
    ("Transport", "UNSD_electricity_Transport row (rail, existing electric road)", "no load of its own: the former method deducted it from Astar as 'embedded' and did not add "
     "it back; table_sectors keeps it in the base load", "Astar block", "base load"),
    ("AgricultureOthers", "agriculture oil rows", "agriculture machinery electric load = oil x electric share / efficiency gain - converts the NON-electric rows only",
     "agriculture block ('agriculture machinery electric')", "explicit (not the electricity row)"),
    ("AgricultureOthers", "UNSD_electricity_AgricultureOthers row", "no load of its own", "Astar block", "base load"),
    ("Residential / Commercial", "biomass cooking rows", "clean-cooking useful-energy load served by electric / gas / LPG stoves (decision 23) - converts the NON-electric rows "
     "only", "buildings block ('cooking electric')", "explicit (not the electricity row)"),
    ("Residential / Commercial", "UNSD_electricity_Residential / _Commercial rows (incl. building cooling)", "no load of its own; building space cooling / heating is not "
     "modelled separately (S1: 'cooling embedded' in Astar)", "Astar block; scenario_network.py S1 docstring", "base load"),
    ("Industry", "industrial low-temperature heat (ratio heat row)", "industry heat load served by heat pump / electric boiler / gas / biomass options (endogenous)",
     "add_industrial_heat", "explicit (heat, not electricity)"),
    ("-", "DAC, electrolysis, synthetic fuels, CO2 capture, storage charging", "endogenous conversion links, not demand-table rows", "s2_layers / scenario layers", "explicit (endogenous)"),
]


def base_by_country(n) -> dict:
    """country -> annual Astar base load read back from the network (MWh)."""
    w = n.snapshot_weightings.generators; L = n.loads[n.loads.account == "Astar"]
    p = n.loads_t.p_set
    return {c: float(sum((p[l] * w).sum() for l in g.index if l in p)) for c, g in L.groupby("country")}


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--main", type=Path, required=True); ap.add_argument("--former", type=Path, required=True); a = ap.parse_args()
    nm, nf = pypsa.Network(str(a.main)), pypsa.Network(str(a.former))
    if nm.meta["s2_demand_ledger"]["parameters"].get("nonindustrial_electricity") != "table_sectors":
        raise ValueError("--main is not a table_sectors build")
    if nf.meta["s2_demand_ledger"]["parameters"].get("nonindustrial_electricity") != "astar_residual":
        raise ValueError("--former is not an astar_residual build")
    dem = pd.read_csv(DEMAND, keep_default_na=False); e = dem[dem.carrier == "electricity"].copy()
    e["v50"] = e.value_2050_mwh.astype(float); e["v19"] = pd.to_numeric(e.base_2019_mwh, errors="coerce").fillna(0.0)
    v50 = e.pivot_table(index="country", columns="sector", values="v50", aggfunc="sum").fillna(0.0) / 1e6
    v19 = e.pivot_table(index="country", columns="sector", values="v19", aggfunc="sum").fillna(0.0) / 1e6
    a5 = pd.read_csv(A5).set_index("country")
    ded_m = {d["country"]: d for d in nm.meta["s2_demand_ledger"]["deductions"]}
    bm, bf = base_by_country(nm), base_by_country(nf)
    rows = []
    for c in sorted(v50.index):
        sec = {s: float(v50.loc[c, s]) if s in v50.columns else 0.0 for s in TABLE_BASE_SECTORS}
        tgt = sum(sec.values()); b19 = sum(float(v19.loc[c, s]) if s in v19.columns else 0.0 for s in TABLE_BASE_SECTORS)
        new, old = bm.get(c, 0.0) / 1e6, bf.get(c, 0.0) / 1e6
        if abs(new - tgt) > 1e-6 * max(1.0, tgt):
            raise ValueError(f"{c}: network base load {new} TWh differs from the table sectors {tgt} TWh")
        rows.append(dict(country=c, residential_twh=sec["Residential"], commercial_twh=sec["Commercial"], agriculture_others_twh=sec["AgricultureOthers"],
                         transport_twh=sec["Transport"], base_load_2050_twh=tgt, base_2019_twh=b19, multiple_vs_2019=(tgt / b19 if b19 else None),
                         industry_electricity_table_twh=float(v50.loc[c, "Industry"]) if "Industry" in v50.columns else 0.0,
                         astar_2050_twh=ded_m[c]["astar_before_mwh"] / 1e6, factor_on_astar=ded_m[c]["factor"],
                         former_astar_residual_twh=old, former_multiple_vs_2019=(old / b19 if b19 else None), change_twh=new - old, network_table_sectors_twh=new,
                         s4i_a5_scheme_b_twh=float(a5.at[c, "alt_table_non_industry_twh"]), minus_s4i_scheme_b_twh=new - float(a5.at[c, "alt_table_non_industry_twh"])))
    T = pd.DataFrame(rows)
    tot = {k: (float(T[k].sum()) if T[k].dtype.kind == "f" else "") for k in T.columns if k != "country"}
    tot.update(country="ASEAN", multiple_vs_2019=tot["base_load_2050_twh"] / tot["base_2019_twh"], former_multiple_vs_2019=tot["former_astar_residual_twh"] / tot["base_2019_twh"],
               factor_on_astar=tot["base_load_2050_twh"] / tot["astar_2050_twh"])
    T = pd.concat([T, pd.DataFrame([tot])], ignore_index=True)
    write_csv(T.to_dict("records"), OUT, list(T.columns))
    write_csv([dict(sector=s, demand_rows=r, model_representation=m, code=loc, in_base_load=b) for s, r, m, loc, b in INVENTORY], INV,
              ["sector", "demand_rows", "model_representation", "code", "in_base_load"])
    A = T.set_index("country")
    reg = Registry(SCRIPT)
    reg.add("s4j1_nonindustrial_electricity_switch", "Decision 104: research.demand.nonindustrial_electricity = table_sectors (main: per country the Astar base load is scaled "
            "to the 2050 demand-table electricity of the sectors not modelled separately; Astar = hourly shape and node split only) | astar_residual (former: Astar minus "
            "the ratio-method industry electricity and the transport electricity; comparison, default when absent)", "table_sectors|astar_residual", "flag", "B",
            "S4J instruction S4J-1", LOC, INSTRUCTION_SHA, decision_ref="104", status="REFERENCE_ONLY")
    reg.add("s4j1_base_load_sectors", "Decision 104: base-load sectors = residential + commercial + agriculture and others + transport electricity of "
            "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv (UNSD 2019 x bridge x AEO8 growth); industry electricity only in the bas_fixed comparison. ASEAN "
            f"{A.at['ASEAN', 'base_load_2050_twh']:.1f} TWh (former {A.at['ASEAN', 'former_astar_residual_twh']:.1f}); VN {A.at['VN', 'base_load_2050_twh']:.1f} TWh "
            f"(former {A.at['VN', 'former_astar_residual_twh']:.1f}, 2019 base {A.at['VN', 'base_2019_twh']:.1f})", float(A.at["ASEAN", "base_load_2050_twh"]) * 1e6, "MWh",
            "B", "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", "research_inputs/demand_v5/NONINDUSTRIAL_ELECTRICITY_S4J1.csv", sha256(OUT),
            decision_ref="104", status="REFERENCE_ONLY")
    reg.add("s4j1_explicit_electricity_inventory", "Decision 104: electricity uses modelled separately and therefore not in the base load (industry route electricity, EV / "
            "FCEV from the land-transport fuel rows, agriculture machinery from the agriculture oil rows, electric cooking from the biomass cooking rows, industrial heat "
            "options, endogenous conversions); the electricity rows of residential, commercial, agriculture and others and transport have no load of their own",
            "table", "flag", "B", "derived (scripts_project/s4j_1_data.py from scripts_project/s2_layers.py)", "research_inputs/demand_v5/EXPLICIT_ELECTRICITY_INVENTORY_S4J1.csv",
            sha256(INV), decision_ref="104", status="REFERENCE_ONLY")
    tr = A.drop(index="ASEAN").transport_twh
    reg.add("s4j1_transport_electricity_row", "Decision 104 finding: the demand-table transport electricity row (rail, existing electric road) was deducted from Astar in the "
            "former method as 'embedded' but no explicit load replaced it (the EV loads convert the non-electric fuel rows only); table_sectors keeps it in the base load. "
            "This is the only difference to the S4I A5 scheme (b) column: " + ", ".join(f"{c} {v:.2f}" for c, v in tr[tr > 0].items()) + " TWh",
            float(tr.sum()) * 1e6, "MWh", "B", "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", "research_inputs/demand_v5/NONINDUSTRIAL_ELECTRICITY_S4J1.csv",
            sha256(OUT), decision_ref="104", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4j_1.csv")
    pd.set_option("display.width", 250)
    print(T[["country", "residential_twh", "commercial_twh", "agriculture_others_twh", "transport_twh", "base_load_2050_twh", "base_2019_twh", "multiple_vs_2019",
             "former_astar_residual_twh", "former_multiple_vs_2019", "change_twh", "s4i_a5_scheme_b_twh", "minus_s4i_scheme_b_twh"]].round(3).to_string())
    (OUT.with_suffix(".json")).write_text(json.dumps(dict(main=str(a.main), former=str(a.former), demand_sha256=sha256(DEMAND), a5_sha256=sha256(A5)), indent=1))


if __name__ == "__main__":
    main()
