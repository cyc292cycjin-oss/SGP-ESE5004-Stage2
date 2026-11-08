"""V4 D2c section 2.1-2.2 (decision 223): measured oil palm trunk dry mass per palm -> energy basis T06 of the trunk pool.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/d2c_trunk_mass.py /home/jin/wt_v4_d2c

1. Per-palm trunk dry mass from the measured sources, each per-hectare value divided by the source's own planting density:
     Khalid, Zin & Anderson 1999 (JOPR 11(1); Kluang, 23 years): 41.07 t DM/ha at 136 palms/ha            (D2b T01 / T04, VERIFIED)
     Chow, Mohd Basri & Chan 2008 (OPB 56, Table 5 note): 136 palms/ha x 274 kg = 37.264 t DM/ha            (D2b T09, VERIFIED)
     Henson 2006 (OPB 52, Fig. 8 polynomial at 25 years after planting = 41.95 t DM/ha; data "adjusted ... to a
       standard of 148 palms per hectare" p. 8; per palm = TSB / PD, Appendix 1 step 1)                      (D2b T12 + D2c H1-H3, VERIFIED)
   centre = median of the three, range = min / max. Other D2b trunk entries are listed with the reason they are not used (secondary quotation,
   estimate, carbon basis, unstated basis, whole palm) and enter only a robustness note.
2. BIOMASS_BASIS_T06.csv = BIOMASS_BASIS_T05.csv with the oil_palm_trunk row replaced (every other line byte-identical, asserted):
     dry matter per reported tonne = trunk dry mass per palm / 2 t per palm (the IRENA 2022 App. A reported mass of the potential chain);
     LHV_dry = 16.12182 GJ/t (the D2b value, instruction 2.1); factor = dry matter per reported t x LHV_dry / 15 (the T05 formula of
     scripts_project/v4_biomass_potential.basis_factors); low / high = the min / max mass at the same LHV; low_rule basis (as T05).
Writes <delivery>/TRUNK_DRY_MASS.csv, <delivery>/evidence/D2C_TRUNK_CALC.json and <repo>/research_inputs/biomass_v5/BIOMASS_BASIS_T06.csv. Nothing is solved.
"""
from __future__ import annotations

import csv
import io
import json
import statistics
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[1]
REPORTED_T_PER_PALM = 2.0      # IRENA 2022 App. A: 2 t per palm (whole above-ground fresh palm, D2b 2.1) - the mass the chain multiplies
LHV_TABLE = 15.0               # GJ/t of the potential table on the reported mass
REPLANT_AGE = 25               # years after planting at replanting: the 25-year cycle of the 4 %/yr replanting rate (unchanged)


def henson_poly(x: float) -> float:
    """Henson 2006 Fig. 8 fitted curve, trunk standing biomass t DM/ha at the standard 148 palms/ha (original: 0.0001x4 - 0.0114x3 + 0.3002x2 - 0..2645x)."""
    return 0.0001 * x ** 4 - 0.0114 * x ** 3 + 0.3002 * x ** 2 - 0.2645 * x


SOURCES = [
    dict(source_id="KHALID1999", source="Khalid H, Zin Z Z, Anderson J M (1999) JOPR 11(1): 23-32", independence_group="G_MPOB_Khalid", included=True,
         value_reported=41.07, unit_reported="t DM/ha", density_palms_per_ha=136.0, density_basis="stand of the destructive sample (Kluang, 23 years; JOPR p. 24)",
         age_years="23", conversion="41.07 t DM/ha / 136 palms/ha", evidence="D2b T01;T04", evidence_grade="VERIFIED",
         note="direct per-palm mean in the same paper 302 kg (270-332, 4 palms); 41.07 = 302 x 136"),
    dict(source_id="CHOW2008", source="Chow M C, Mohd Basri W, Chan K W (2008) Oil Palm Bulletin 56: 23-28", independence_group="G_MPOB_Chow", included=True,
         value_reported=37.264, unit_reported="t DM/ha", density_palms_per_ha=136.0, density_basis="Table 5 note: 136 palms per ha at 274 kg per trunk (dwb)",
         age_years="~25 (economic life)", conversion="37.264 t DM/ha (= 136 x 274 kg) / 136 palms/ha", evidence="D2b T09", evidence_grade="VERIFIED",
         note="the decision text rounds to 37.3 t DM/ha"),
    dict(source_id="HENSON2006", source="Henson I E (2006) Oil Palm Bulletin 52: 1-24, Fig. 8 and Appendix 1", independence_group="G_MPOB_Henson", included=True,
         value_reported=None, unit_reported="t DM/ha", density_palms_per_ha=148.0,
         density_basis="p. 8: Fig. 8 data adjusted to a standard of 148 palms per hectare; Appendix 1 step 1: TBPP = TSB / PD x 1000",
         age_years=str(REPLANT_AGE), conversion=f"Fig. 8 polynomial at {REPLANT_AGE} years after planting / 148 palms/ha", evidence="D2b T12; D2c H1;H2;H3",
         evidence_grade="VERIFIED",
         note="compilation: the Fig. 8 points include Khalid 1999 (KLU) and Corley 1971b (WM), so it is not fully independent of KHALID1999; "
              "23 / 27 years give 0.2838 / 0.2734 t DM/palm (centre unchanged, the median stays the Henson value from 23 to 26 years)"),
    dict(source_id="HUSIN_POD36", source="Mohamad Husin et al., Palm Oil Developments 36: 1-5 (MPOB)", independence_group="G_MPOB_Husin", included=False,
         value_reported=0.600, unit_reported="t DM/palm", density_palms_per_ha=145.0, density_basis="145 palms/ha, 95 % survival (stated)", age_years="25",
         conversion="per palm as stated", evidence="D2b T07", evidence_grade="VERIFIED",
         note="not used: an estimate carried from Mohd Husin et al. 1985, not a measurement on the page (D2b T07); about twice the measured values"),
    dict(source_id="CORLEY1971", source="Corley R H V et al. (1971), quoted by Khalid 1999 p. 28", independence_group="secondary", included=False,
         value_reported=0.300, unit_reported="t DM/palm", density_palms_per_ha=None, density_basis="-", age_years="27.5", conversion="per palm as quoted",
         evidence="D2b T05", evidence_grade="SNIPPET", note="not used: secondary quotation (original not read); the Corley 1971b data are already points of Henson Fig. 8 (WM)"),
    dict(source_id="TINKER_SMILDE1963", source="Tinker & Smilde (1963), quoted by Khalid 1999 p. 28", independence_group="secondary", included=False,
         value_reported=0.344, unit_reported="t DM/palm", density_palms_per_ha=None, density_basis="-", age_years="22 (Nigeria)", conversion="per palm as quoted",
         evidence="D2b T06", evidence_grade="SNIPPET", note="not used: secondary quotation (original not read), West African material"),
    dict(source_id="SISWOKO2018", source="Siswoko et al. (2018) UNRI repository (abstract)", independence_group="secondary", included=False,
         value_reported=0.22368, unit_reported="t C/palm", density_palms_per_ha=None, density_basis="-", age_years="25", conversion="carbon / 0.419-0.47 -> 0.476-0.534 t DM (derived)",
         evidence="D2b T25", evidence_grade="SNIPPET", note="not used: abstract only, carbon basis (dry mass derived)"),
    dict(source_id="HAMBALI2017", source="Hambali & Rivai (2017) IOP EES 65: 012050, Table 5", independence_group="G_IPB_Hambali", included=False,
         value_reported=75.50, unit_reported="t/ha (basis not stated)", density_palms_per_ha=143.0, density_basis="143 palms/ha (stated)", age_years="25-30",
         conversion="75.50 / 143 = 0.528 t per palm", evidence="D2b T21", evidence_grade="VERIFIED", note="not used: fresh / dry basis not stated"),
    dict(source_id="WARDANI2013", source="Wardani (2013) IPB repository (abstract)", independence_group="G_IPB", included=False,
         value_reported=76.75, unit_reported="t DM/ha (whole palm incl. roots)", density_palms_per_ha=None, density_basis="-", age_years="not stated",
         conversion="-", evidence="D2b T24", evidence_grade="SNIPPET", note="not used: whole palm including fronds and roots, no trunk value"),
]


def per_palm(s: dict) -> float | None:
    if s["source_id"] == "HENSON2006":
        return henson_poly(REPLANT_AGE) / s["density_palms_per_ha"]
    if s["unit_reported"] == "t DM/ha" and s["density_palms_per_ha"]:
        return s["value_reported"] / s["density_palms_per_ha"]
    if s["unit_reported"] == "t DM/palm":
        return s["value_reported"]
    return None


def main():
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/jin/wt_v4_d2c")
    lhv = 16.12182   # GJ/t dry; D2b BIOMASS_BASIS_T05.csv lhv_dry_gj_t_mid (median of Chow 2008 16.152 / Umar 2020 16.091)
    rows = []
    for s in SOURCES:
        r = dict(s)
        if s["source_id"] == "HENSON2006":
            r["value_reported"] = henson_poly(REPLANT_AGE)
        m = per_palm(r)
        r["per_palm_t_dm"] = m
        r["per_ha_at_model_140_t_dm"] = None if m is None else 140.0 * m
        rows.append(r)
    inc = [r for r in rows if r["included"]]
    vals = [r["per_palm_t_dm"] for r in inc]
    mid, lo, hi = statistics.median(vals), min(vals), max(vals)
    dm = dict(mid=mid / REPORTED_T_PER_PALM, low=lo / REPORTED_T_PER_PALM, high=hi / REPORTED_T_PER_PALM)
    fac = {k: v * lhv / LHV_TABLE for k, v in dm.items()}
    robust = {}
    for tag, extra in (("plus_tinker_smilde", ["TINKER_SMILDE1963"]), ("plus_husin", ["HUSIN_POD36"]), ("plus_corley_tinker_husin", ["CORLEY1971", "TINKER_SMILDE1963", "HUSIN_POD36"])):
        v = vals + [r["per_palm_t_dm"] for r in rows if r["source_id"] in extra]
        robust[tag] = dict(median=statistics.median(v), min=min(v), max=max(v), n=len(v))
    henson_age = {str(x): dict(t_dm_per_ha=henson_poly(x), t_dm_per_palm=henson_poly(x) / 148.0,
                               median_of_three=statistics.median([0.274, 41.07 / 136.0, henson_poly(x) / 148.0])) for x in (23, 24, 25, 26, 27)}
    t05 = dict(factor_mid=0.3134798333333334, dry_matter_per_reported_t=0.29166666666666674)
    t05["equivalent_dry_mass_per_palm_t"] = t05["dry_matter_per_reported_t"] * REPORTED_T_PER_PALM

    # TRUNK_DRY_MASS.csv (delivery)
    cols = ["source_id", "source", "independence_group", "included", "value_reported", "unit_reported", "density_palms_per_ha", "density_basis", "age_years",
            "conversion", "per_palm_t_dm", "per_ha_at_model_140_t_dm", "evidence", "evidence_grade", "note"]
    summ = [
        dict(source_id="CENTRE", source="median of the included sources", included="", per_palm_t_dm=mid, per_ha_at_model_140_t_dm=140 * mid,
             note=f"factor on the W08 energy = {mid:.6f} / 2 x {lhv} / 15 = {fac['mid']:.6f} (T05 0.313480)"),
        dict(source_id="LOW", source="minimum of the included sources", included="", per_palm_t_dm=lo, per_ha_at_model_140_t_dm=140 * lo, note=f"factor {fac['low']:.6f}"),
        dict(source_id="HIGH", source="maximum of the included sources", included="", per_palm_t_dm=hi, per_ha_at_model_140_t_dm=140 * hi, note=f"factor {fac['high']:.6f}"),
        dict(source_id="T05_EQUIVALENT", source="D2b T05 (high-sensitivity switch value v4_adjusted_t05): 2 t fresh x dry matter 0.2917", included="",
             per_palm_t_dm=t05["equivalent_dry_mass_per_palm_t"], per_ha_at_model_140_t_dm=140 * t05["equivalent_dry_mass_per_palm_t"], note="factor 0.313480"),
    ]
    buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n"); w.writeheader()
    for r in rows + summ:
        w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.6f}" if isinstance(r.get(k), float) else r.get(k, ""))) for k in cols})
    (W / "TRUNK_DRY_MASS.csv").write_text(buf.getvalue(), encoding="utf-8", newline="\n")

    # BIOMASS_BASIS_T06.csv (repository): T05 with the trunk row replaced
    src = repo / "research_inputs/biomass_v5/BIOMASS_BASIS_T05.csv"
    text = src.read_text(encoding="utf-8")
    rdr = list(csv.DictReader(io.StringIO(text)))
    fields = list(rdr[0].keys())
    n_trunk = 0
    for r in rdr:
        if r["category"] != "oil_palm_trunk":
            continue
        n_trunk += 1
        r.update(origin="T06 (D2c)",
                 mass_basis=("measured trunk dry mass per palm (median of Chow 2008 0.274 @136/ha, Henson 2006 0.2834 @148/ha 25 YAP, Khalid 1999 0.3020 @136/ha) "
                             "per reported 2 t per palm of the chain (IRENA 2022 App. A: whole above-ground fresh palm) - TRUNK_DRY_MASS.csv of the D2c delivery"),
                 moisture_reported_mid="", moisture_reported_low="", moisture_reported_high="",
                 dry_matter_mid=repr(dm["mid"]), dry_matter_low=repr(dm["low"]), dry_matter_high=repr(dm["high"]),
                 lhv_dry_gj_t_mid=repr(lhv), lhv_dry_gj_t_low=repr(lhv), lhv_dry_gj_t_high=repr(lhv))
        d = float(r["dry_matter_mid"]); L = float(r["lhv_dry_gj_t_mid"]); tab = float(r["lhv_table_gj_t"])
        r.update(energy_per_reported_t_mid=repr(d * L), factor_mid=repr(d * L / tab), factor_low=repr(float(r["dry_matter_low"]) * L / tab),
                 factor_high=repr(float(r["dry_matter_high"]) * L / tab), verdict="INCONSISTENT", applied="True", low_rule="basis", grade="C",
                 sources="T04;T09;T12 (D2b TRUNK_LITERATURE.json);H1;H2;H3 (D2c D2C_TRUNK_LITERATURE.json)",
                 rule=(f"D2c 2.1 (decision 223): measured trunk dry matter x LHV_dry instead of the whole-palm fresh mass (T05 = high-sensitivity switch value "
                       f"v4_adjusted_t05): per palm {mid:.4f} t DM (median of three; range {lo:.4f}-{hi:.4f}) / 2 t reported x {lhv} GJ/t / 15 = {d * L / tab:.6f}; "
                       "low / high = min / max per-palm mass at the same LHV (the LHV range 16.09-17.47 stays in registry v4_oil_palm_trunk_lhv_dry); "
                       "replanting 4 %/yr (25-year cycle) and harvest cap 0.25 unchanged; replanting low 2.2 %/yr = registry v4_oil_palm_replanting_rate (SENSITIVITY)"))
    assert n_trunk == 1
    out = io.StringIO(); w = csv.DictWriter(out, fieldnames=fields, lineterminator="\n"); w.writeheader()
    for r in rdr:
        w.writerow(r)
    new = out.getvalue()
    a, b = text.split("\n"), new.split("\n")
    assert len(a) == len(b), (len(a), len(b))
    changed = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert len(changed) == 1 and a[changed[0]].startswith("oil_palm_trunk,"), changed   # every other line byte-identical to T05
    dst = repo / "research_inputs/biomass_v5/BIOMASS_BASIS_T06.csv"
    dst.write_text(new, encoding="utf-8", newline="\n")

    calc = dict(instruction="V4_D2C_INSTRUCTION.md section 2.1 (decision 223)", lhv_dry_gj_t=lhv, reported_t_per_palm=REPORTED_T_PER_PALM, lhv_table_gj_t=LHV_TABLE,
                replant_age_years=REPLANT_AGE, sources=rows, centre_t_dm_per_palm=mid, low_t_dm_per_palm=lo, high_t_dm_per_palm=hi,
                dry_matter_per_reported_t=dm, factor=fac, t05=t05, ratio_t06_over_t05=fac["mid"] / t05["factor_mid"], robustness_of_centre=robust, henson_age=henson_age,
                per_ha_at_model_density_140=dict(mid=140 * mid, low=140 * lo, high=140 * hi),
                basis_table=dict(path=str(dst.relative_to(repo)), changed_line=changed[0], t05_lines=len(a)))
    (W / "evidence").mkdir(exist_ok=True)
    (W / "evidence/D2C_TRUNK_CALC.json").write_text(json.dumps(calc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(f"centre {mid:.6f} low {lo:.6f} high {hi:.6f} t DM/palm | factor mid {fac['mid']:.6f} low {fac['low']:.6f} high {fac['high']:.6f} | T06/T05 {fac['mid'] / t05['factor_mid']:.6f}")
    print("robustness", {k: round(v["median"], 5) for k, v in robust.items()})
    print("wrote", dst, "changed line", changed[0])


if __name__ == "__main__":
    main()
