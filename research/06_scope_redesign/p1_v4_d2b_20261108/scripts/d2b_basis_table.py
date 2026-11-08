"""V4 D2b section 2 (decision 221): the energy-basis audit table of every biomass category, research_inputs/biomass_v5/BIOMASS_BASIS_T05.csv, read by
scripts_project/v4_biomass_potential.py basis_factors("t05") (research.demand.v4.biomass_potential = v4_adjusted_t05, the v4 main set).

    python scripts/d2b_basis_table.py <repo>

Rule (instruction section 2.3, registered by the instruction itself, = D2a section 3.2):
  mass basis and heating-value basis inconsistent -> recompute as dry matter x LHV_dry (factor = dry_matter_per_reported_t x LHV_dry / lhv_table); the old value
                                                     stays the switch alternative (v4_adjusted_t04 / v4_adjusted / v3);
  consistent                                      -> keep the current value, upgrade the sources;
  sources contradict each other, undecidable      -> keep the current value, give a range, refer to the reviewer.
Every category gets a low / high range (factor_low / factor_high on the T04-main energy of the category).
Mid values = median of the independent primary source groups (one value per group); low / high = the extreme source values (or the combination of the
extreme moisture and LHV values). Evidence ids refer to evidence/*_LITERATURE.json of the D2b delivery (T = trunk, R = residues) and to the D2a
T04_LITERATURE.json (E..). Nothing is solved; the script writes the table only.
"""
from __future__ import annotations

import csv
import statistics as st
import sys
from pathlib import Path

COLS = ["category", "part", "origin", "mass_basis", "heat_basis_table", "lhv_table_gj_t", "moisture_reported_mid", "moisture_reported_low", "moisture_reported_high",
        "dry_matter_mid", "dry_matter_low", "dry_matter_high", "lhv_dry_gj_t_mid", "lhv_dry_gj_t_low", "lhv_dry_gj_t_high", "energy_per_reported_t_mid",
        "factor_mid", "factor_low", "factor_high", "verdict", "applied", "low_rule", "grade", "sources", "rule"]


def med(xs):
    return float(st.median(xs))


def row(category, origin, mass_basis, heat_basis, lhv_table, moist, lhv_dry, verdict, applied, low_rule, grade, sources, rule, part="all", f_override=None):
    """moist = (mid, low_moisture, high_moisture) of the reported mass (wet basis); lhv_dry = (mid, low, high) GJ/t dry. dry_matter = 1 - moisture.
    factor_low = (1 - high moisture) x low LHV / lhv_table; factor_high = (1 - low moisture) x high LHV / lhv_table. f_override = (mid, low, high) for the
    consistent / undetermined rows (no recomputation: factor_mid = 1)."""
    r = dict(category=category, part=part, origin=origin, mass_basis=mass_basis, heat_basis_table=heat_basis, lhv_table_gj_t=lhv_table, verdict=verdict,
             applied=applied, low_rule=low_rule, grade=grade, sources=sources, rule=rule)
    if moist is not None:
        m, ml, mh = moist
        r.update(moisture_reported_mid=m, moisture_reported_low=ml, moisture_reported_high=mh, dry_matter_mid=1.0 - m, dry_matter_low=1.0 - mh, dry_matter_high=1.0 - ml)
    if lhv_dry is not None:
        r.update(lhv_dry_gj_t_mid=lhv_dry[0], lhv_dry_gj_t_low=lhv_dry[1], lhv_dry_gj_t_high=lhv_dry[2])
    if f_override is not None:
        r.update(factor_mid=f_override[0], factor_low=f_override[1], factor_high=f_override[2])
    else:
        dm, dml, dmh = r["dry_matter_mid"], r["dry_matter_low"], r["dry_matter_high"]
        r.update(factor_mid=dm * lhv_dry[0] / lhv_table, factor_low=dml * lhv_dry[1] / lhv_table, factor_high=dmh * lhv_dry[2] / lhv_table)
    if moist is not None and lhv_dry is not None:
        r["energy_per_reported_t_mid"] = r["dry_matter_mid"] * lhv_dry[0]
    return r


def rows():
    R = []
    # ---- palm mill residues: the D2a T04 rows carried over (same factors; PALM_RESIDUE_BASIS_T04.csv, D2a evidence/T04_LITERATURE.json)
    R.append(row("oil_palm_efb", "T04 (D2a)", "wet (IRENA 2022 Box 4 mill mass balance; Abdullah & Sulaiman 2013 wet 22.0 % / dry 14.6 %)", "15 GJ/t (IRENA 2017a convention, dry-basis magnitude)",
                 15.0, (0.60, 0.572, 0.67), (18.0, 15.83, 19.09), "INCONSISTENT (D2a T04)", True, "scale", "C", "E01;E05;E12;E13;E14;E10;E17 (D2a)",
                 "D2a T04 carried over: (1 - 0.60) x 18.0 = 7.2 GJ per wet t (x 0.48)"))
    R.append(row("oil_palm_fibre", "T04 (D2a)", "wet (IRENA 2022 Box 4; Abdullah & Sulaiman 2013 wet 13.5 % / dry 15.4 %)", "15 GJ/t", 15.0, (0.37, 0.364, 0.372), (18.1, 17.86, 18.32),
                 "INCONSISTENT (D2a T04)", True, "scale", "C", "E01;E06;E08;E13;E17 (D2a)", "D2a T04 carried over: (1 - 0.37) x 18.1 = 11.4 GJ per wet t (x 0.7602); main set removes 100 % in the mills (T03)"))
    R.append(row("oil_palm_pks", "T04 (D2a)", "wet (IRENA 2022 Box 4)", "15 GJ/t", 15.0, (0.12, 0.084, 0.214), (19.3, 18.50, 20.02), "CONSISTENT (D2a T04)", False, "scale", "B",
                 "E07;E09;E12;E13;E17 (D2a)", "D2a T04 carried over: 15 GJ/t inside the as-received LHV range 14.0-18.1 GJ/t; kept", f_override=(1.0, 0.933, 1.209)))
    # ---- oil palm trunk (D2b 2.1): INCONSISTENT -> applied
    w_groups = {"Khalid 1999 (MPOB) T04": 0.80, "Chow 2008 (MPOB) T10": 0.76, "Husin POD 36 (MPOB) T08": (2 / 3 + 3 / 4) / 2, "Abdullah & Sulaiman 2013 E13 (D2a)": 0.70,
                "Fakhri 2016 via Fakhri 2023 T20": (0.581 + 0.775) / 2}
    lhv_groups = {"Chow 2008 HHV 17.471 dwb, H 6.0 % -> LHV T11": 17.471 - 2.442 * 9 * 0.060, "Umar 2020 HHV 17.41 near-dry, H 6.0 % -> LHV T13": 17.41 - 2.442 * 9 * 0.060}
    wm, lm = med(list(w_groups.values())), med(list(lhv_groups.values()))
    w_lo, w_hi = min(w_groups.values()), max(w_groups.values())
    l_lo, l_hi = min(lhv_groups.values()), 17.471   # high: the dry-basis HHV of Chow 2008 taken as the upper bound of the LHV
    f_low_mass = 0.274 * l_lo / 30.0   # mass variant: measured trunk dry mass 0.274 t per palm (Chow 2008 T09) instead of 2 t fresh x dry matter; x LHV low / 30 GJ per palm (2 t x 15)
    tr = row("oil_palm_trunk", "T05 (D2b)", "fresh (IRENA 2022 App. A p.138: 2 t per OPT with 80 % water; per ha 280 t vs literature trunk fresh ~205 t/ha and trunk dry 37-42 t DM/ha; per t FFB 0.65 vs trunk fresh 0.43 / dry 0.086 - TRUNK_CHAIN_CHECK.csv)",
             "15 GJ/t on the reported (fresh) mass (IRENA 2017a convention)", 15.0, (wm, w_lo, w_hi), (lm, l_lo, l_hi), "INCONSISTENT", True, "basis", "C",
             "T01;T02;T04;T07;T08;T09;T10;T11;T12;T13;T20;E13(D2a);E11(D2a)",
             f"D2b 2.1: fresh mass x 15 GJ/t -> dry matter x LHV_dry; moisture = median of 5 author groups {', '.join(f'{v:.3f}' for v in w_groups.values())} = {wm:.4f}; LHV_dry = median of "
             f"{', '.join(f'{v:.3f}' for v in lhv_groups.values())} = {lm:.4f} GJ/t; factor = (1 - {wm:.4f}) x {lm:.4f} / 15; low = mass variant (measured trunk dry mass 0.274 t/palm x LHV "
             f"{l_lo:.3f} / 30 GJ per palm) = {f_low_mass:.4f}; high = (1 - {w_lo:.3f}) x 17.471 / 15. The IRENA mass 2 t/palm itself is the whole above-ground fresh palm "
             "(Khalid 1999: trunk 1.51 t, whole palm 2.0-2.4 t) - a residue-factor question kept for the reviewer; harvest cap 0.25 unchanged")
    tr["factor_low"] = f_low_mass
    R.append(tr)
    # ---- agricultural residues (D2b 2.2): Smeets h = 1/HI - 1 (Smeets 2007 PECS 5.1, dry-weight framework), applied by IRENA 2017a to FAOSTAT production
    #      (fresh / field weight) x 15 GJ/t (IRENA REmap 2014: 'LHV 15 GJ/t, air dry 12-14 % water'). Measured RPRs on the air-dry basis reproduce the factors
    #      for rice / maize / sugarcane tops / coconut process -> consistent; cassava, coconut harvest (palm-kernel group factor 3.0) and the fruit / vegetable
    #      rows cannot be reproduced on any basis -> undetermined (kept, range, reviewer).
    R.append(row("rice_residues", "T05 (D2b)", "air-dry residue per t paddy (straw RPR 0.45-1.76 at 12.7 %, husk 0.267 at 12.4 %; Smeets h 1.3 / p 0.2)", "15 GJ/t air-dry LHV (REmap 2014 convention)",
                 15.0, (0.127, 0.095, 0.14), (14.87, 14.87, 15.96), "CONSISTENT", False, "scale", "C", "R03;R05;R06;R13;R14;R26;R30;R31;Smeets2007",
                 "kept (basis consistent; air-dry measured LHV 13.5-14.0, dry 14.9-16.0); low = (1 - 0.127) x 14.87 / 15 (straw, dry matter x LHV_dry); high = 1.0",
                 f_override=(1.0, (1 - 0.127) * 14.87 / 15.0, 1.0)))
    R.append(row("maize_residues", "T05 (D2b)", "air-dry residue per t grain (stalk 2.0 at 15 %, cob 0.273 at 7.5 %; Smeets h 1.5 / p 0.2)", "15 GJ/t air-dry LHV", 15.0, (0.15, 0.0807, 0.15),
                 (15.64, 15.64, 16.82), "CONSISTENT", False, "scale", "C", "R06;R15;R34;R35;Smeets2007",
                 "kept; fresh stalks (68.5 %, LHV 4.9) would be inconsistent but the factor matches the air-dry RPR; low = (1 - 0.15) x 15.64 / 15; high = (1 - 0.0807) x 16.82 / 15",
                 f_override=(1.0, (1 - 0.15) * 15.64 / 15.0, (1 - 0.0807) * 16.82 / 15.0)))
    R.append(row("sugarcane_residues", "T05 (D2b)", "tops / leaves 0.3 per t cane = air-dry RPR (USAID 0.3 at 10 %) vs 0.265 fresh (Junginger 2000); bagasse part = W12 R2 (UNSD wet bagasse x 7.718 GJ/t NCV) where UNSD reports",
                 "15 GJ/t (tops / leaves); UNSD NCV 7.718 GJ/t wet (bagasse after F3)", 15.0, (0.10, 0.10, 0.40), (15.96, 15.96, 16.70), "CONSISTENT", False, "scale", "C",
                 "R17;R18;R26;R27;R28;R32;R33;R41;W12",
                 "kept (tops / leaves air-dry; bagasse wet x wet NCV after F3, decision 209); tops / leaves low = fresh reading 0.265 / 0.3 x (1 - 0.40) x 15.96 / 15 = 0.564 on that part; "
                 "bagasse high = dry matter x LHV_dry (1 - 0.5148) x 16.70 / 7.718 = 1.050 on that part; category range 0.80-1.03 (INFERENCE, harvest share ~35 %)",
                 f_override=(1.0, 0.80, 1.03)))
    R.append(row("coconut_residues", "T05 (D2b)", "process 0.5 per t nut = air-dry husk 0.419 + shell 0.12 (Bhattacharya 1993); harvest 3.0 = the IRENA 2017a 'Palm kernels' group factor applied to coconuts (fronds ~0.24-0.5 t dry per t nut, INFERENCE)",
                 "15 GJ/t", 15.0, (0.10, 0.087, 0.118), (17.59, 17.25, 17.59), "UNDETERMINED", False, "scale", "D", "R03;R19;R20;R36",
                 "kept: process part consistent (coir LHV ar 15.5); harvest factor 3.0 not reproduced on any basis (palm-kernel group factor) -> reviewer; low = harvest part x 0.1 "
                 "(0.45 + 0.075) / 1.2 = 0.44; high 1.0", f_override=(1.0, (0.45 + 0.075) / 1.2, 1.0)))
    R.append(row("cassava_residues", "T05 (D2b)", "Smeets h 1.0 per t FRESH root vs measured stalks 0.06-0.2 t air-dry / dry per t fresh root (Koopmans 1997; rhizome 0.112 wet); only a fresh stems+leaves ratio (0.22-0.83) reaches 1.0",
                 "15 GJ/t", 15.0, None, None, "UNDETERMINED", False, "scale", "D", "R16;R26;R38;R48;Smeets2007",
                 "kept: the factor cannot be reproduced on any basis (dry HI reading x tuber dry matter 0.22-0.35, or fresh stems x (1 - 0.6)) -> both readings 0.25-0.45 of the value; "
                 "reviewer / W19; low = 0.22 x 17 / 15 = 0.25 (IPCC tuber dry matter x LHV_dry), high 1.0", f_override=(1.0, 0.22 * 17.0 / 15.0, 1.0)))
    R.append(row("other_crop_residues", "T05 (D2b)", "Smeets fruit 2.03 / vegetables 0.41 per t FRESH product (bananas, fruit, vegetables 80-90 % water); no ASEAN primary RPR read", "15 GJ/t", 15.0, None, None,
                 "UNDETERMINED", False, "scale", "D", "R06;R38;Smeets2007",
                 "kept: if h is a dry-matter ratio (Smeets 2007 dry-weight framework) applied to fresh fruit / vegetables the potential is overstated ~5-7 x; no measured ASEAN RPR -> reviewer / W19; "
                 "low = 0.15 x 16 / 15 = 0.16 (product dry matter 0.15 x LHV_dry), high 1.0", f_override=(1.0, 0.15 * 16.0 / 15.0, 1.0)))
    R.append(row("wood_processing_residues", "T05 (D2b)", "solid m3 of residue = log input x (1 - recovery) (FAO/APFC 2001)", "9.14 GJ/m3 = UNSD NCV fuelwood / wood residues, solid volume, 20-30 % moisture",
                 9.14, None, None, "CONSISTENT", False, "scale", "B", "R40;R41;R42;R43;R47;R39",
                 "kept, source upgraded (UNSD Energy Balances 2022 p.xxv-xxvi); range 8.4-10.0 GJ/m3 (Tun 2019; FAO UBET 0.725 t/m3 x 13.8)", f_override=(1.0, 8.4 / 9.14, 10.0 / 9.14)))
    R.append(row("msw_organic_biogas", "T05 (D2b)", "wet mass (What a Waste) x IPCC wet-basis DOC", "methane LHV 50.04 GJ/t CH4", 50.04, None, None, "CONSISTENT", False, "scale", "B", "IPCC2006 V5 Ch2-3 (v3 table)",
                 "kept (wet basis stated on both sides)", f_override=(1.0, 1.0, 1.0)))
    R.append(row("oil_palm_pome", "T05 (D2b)", "POME 0.583 t per t FFB (IRENA 2022 Box 4)", "0.69 GJ biogas per t POME (IRENA 2022 Table 11 implied)", 0.69, None, None, "CONSISTENT", False, "scale", "C", "E01;E02 (D2a)",
                 "kept (energy per tonne of the liquid as generated)", f_override=(1.0, 1.0, 1.0)))
    return R


def main():
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/jin/wt_v4_d2b")
    out = repo / "research_inputs/biomass_v5/BIOMASS_BASIS_T05.csv"
    R = rows()
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        for r in R:
            w.writerow({k: (repr(float(v)) if isinstance(v, float) else v) for k, v in r.items()})
    print(out, len(R))


if __name__ == "__main__":
    main()
