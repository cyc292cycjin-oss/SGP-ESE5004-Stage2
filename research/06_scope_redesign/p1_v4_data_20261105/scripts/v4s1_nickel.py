"""V4 S1 section 3: the base year of Indonesian nickel in v3.

    PYTHONHASHSEED=0 python scripts/v4s1_nickel.py --work <work dir> --repo /home/jin/wt_v4_data      (WSL pypsa-earth python)

1. From the repository v3 tables (NONFERROUS_PRODUCTION_V3.csv, NICKEL_ENERGY_WEI2020.csv, INDUSTRY_V3_EVIDENCE.json, INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv):
   2019 Ni-content production and energy; v3 main 2050 activity and energy; USGS 2023 actual production (MYB 2023 Indonesia table 1, read again from the
   PDF text) and its energy at the same unit energy.
2. Check of the reviewer's inference (v3 main 2050 nickel activity below the 2023 actual). Option 'nickel on the 2023 base' (only nickel; the v3
   NF2023 case moves every non-ferrous metal) quantified with v3_industry.decompose / nonferrous and the D163-6 a conservation: ID nickel, the other
   bucket and its carriers. Not implemented.
3. Unit energy: source and process of Wei et al. 2020 Case 3-FeNi; the 2019 / 2023 product mix (NPI, ferronickel, matte, MHP) and Ni grades from USGS.
Output s1/ID_NICKEL_BASEYEAR.csv and s1/_nickel_evidence.json. Read-only; nothing is solved.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4s1_common as cm   # noqa: E402
import re   # noqa: E402

USGS_DIR = "extracted/usgs_myb3_2023_id/myb3-2023-indonesia"


def usgs_line(work: Path, start: str) -> list:
    """2019-2023 values of the USGS MYB 2023 Indonesia table 1 line that starts with `start` ('--' = 0; footnote marks r, e dropped)."""
    for line in (work / USGS_DIR / "p006.txt").read_text(encoding="utf-8").splitlines():
        s = re.sub(r"\s+", " ", line).strip()
        if s.startswith(start):
            lab = re.match(r"^(\D*?)(?=\s(?:\d|--))", s).group(1)
            toks = [t for t in s[len(lab):].replace(",e", "").split() if t not in ("r,", "e", "r", "r,e")]
            vals = [0.0 if t == "--" else float(t.replace(",", "")) for t in toks if re.fullmatch(r"--|\d{1,3}(,\d{3})*", t)]
            if len(vals) != 5:
                raise ValueError(f"USGS line '{s}': {vals}")
            return vals
    raise KeyError(start)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); ap.add_argument("--repo", type=Path, default=cm.REPO); a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    import v3_industry as v3   # noqa: E402
    R = a.repo / "research_inputs"
    nf = pd.read_csv(R / "industry_v3/NONFERROUS_PRODUCTION_V3.csv")
    ni = nf[nf.route == "nickel"]
    ne = v3.nickel_unit_energy(); fut = v3.future_vectors()
    ev3 = json.loads((R / "industry_v3/INDUSTRY_V3_EVIDENCE.json").read_text())
    sub = pd.read_csv(R / "industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv"); sid = sub[sub.country == "ID"]
    usg = {k: usgs_line(a.work, lab) for k, lab in (("npi_ni", "Nickel pig irone 380,000"), ("npi_gross", "Nickel pig irone 3,200,000"), ("feni_ni", "Ferronickel 25,713"),
                                                    ("feni_gross", "Ferronickele 129,000"), ("matte_ni", "Smelter, matte"), ("mhp_ni", "Intermediate, mixed hydroxide precipitate"),
                                                    ("mine_ni", "Mine, laterite ore"))}
    rows = []
    q19 = float(ni.q_2019_t.sum()); q23 = float(ni.q_2023_t.sum())
    if abs(q23 - (usg["npi_ni"][-1] + usg["feni_ni"][-1] + usg["matte_ni"][-1])) > 1:
        raise ValueError(f"repository q_2023 {q23} != USGS 2023 NPI + FeNi + matte")
    el, fu, uh = ne["electricity_mwh_per_t_ni"], ne["fuel_mwh_per_t_ni"], ne["useful_heat_mwh_per_t_ni"]
    led = ev3["cases"]["main"]["nonferrous"]["ID:nonferrous_nickel"]; led23 = ev3["cases"]["nf2023"]["nonferrous"]["ID:nonferrous_nickel"]
    m50 = sid[(sid.case == "main") & (sid.subsector == "nonferrous_nickel")].set_index("carrier").mwh_2050 / 1e6
    n50 = sid[(sid.case == "nf2023") & (sid.subsector == "nonferrous_nickel")].set_index("carrier").mwh_2050 / 1e6

    def add(item, ni_t, el_twh, heat_twh, fuel_twh, source, grade, status):
        rows.append(dict(item=item, ni_content_t=ni_t, electricity_twh=el_twh, useful_heat_gt400_twh=heat_twh, fuel_input_twh=fuel_twh,
                         total_model_twh=el_twh + heat_twh, source=source, grade=grade, status=status))
    for r in ni.itertuples():
        add(f"2019 {r.commodity}", r.q_2019_t, r.q_2019_t * el / 1e6, r.q_2019_t * uh / 1e6, r.q_2019_t * fu / 1e6, r.source_locator, r.tier, "VERIFIED")
    add("2019 total (v3 base)", q19, q19 * el / 1e6, q19 * uh / 1e6, q19 * fu / 1e6, "NONFERROUS_PRODUCTION_V3.csv x Wei 2020 Case 3-FeNi", "B / C", "VERIFIED")
    add("2050 v3 main (2019 x growth)", led["q_2050_t"], float(m50.get("electricity", 0)), float(m50.get("heat_high", 0)), led["q_2050_t"] * fu / 1e6,
        f"INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv case main; growth {led['growth_factor']:.6f}", "C", "VERIFIED")
    for r in ni.itertuples():
        add(f"2023 {r.commodity} (USGS actual)", r.q_2023_t, r.q_2023_t * el / 1e6, r.q_2023_t * uh / 1e6, r.q_2023_t * fu / 1e6, r.source_locator, r.tier, "VERIFIED")
    add("2023 total (USGS actual, v3 routes)", q23, q23 * el / 1e6, q23 * uh / 1e6, q23 * fu / 1e6, "same unit energy as v3", "B / C", "VERIFIED")
    add("2023 MHP (HPAL) not in the v3 routes", usg["mhp_ni"][-1], float("nan"), float("nan"), float("nan"), "USGS MYB 2023 Indonesia table 1 (2023 estimated)", "B", "VERIFIED (gap)")
    add("2050 v3 NF2023 sensitivity (2023 x growth)", led23["q_2050_t"], float(n50.get("electricity", 0)), float(n50.get("heat_high", 0)), led23["q_2050_t"] * fu / 1e6,
        f"case nf2023; growth {led23['growth_factor']:.6f}", "C", "VERIFIED")
    # ---- option: nickel only on the 2023 base, ID other bucket by the conservation rule -----------------------------------
    T_row = pd.read_csv(R / "demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv").set_index("country").loc["ID"]
    T = float(sum(T_row[v3.col(x)] for x in v3.CARRIERS))
    parts0 = v3.decompose(T_row, fut)
    out = {}
    for case, nfc in (("main", v3.nonferrous(fut, "main", ne)[0]["ID"]), ("nf2023_all", v3.nonferrous(fut, "nf2023", ne)[0]["ID"])):
        out[case] = nfc
    out["nickel_only_2023"] = dict(out["main"]); out["nickel_only_2023"]["nonferrous_nickel"] = out["nf2023_all"]["nonferrous_nickel"]
    res = {}
    for case, nfc in out.items():
        parts = {k: dict(v) for k, v in parts0.items()}; parts.update(nfc)
        expl = sum(sum(v.values()) for k, v in parts.items() if k != "other"); so = sum(parts["other"].values()); f = (T - expl) / so
        oth = {k: v * f / 1e6 for k, v in parts["other"].items()}
        res[case] = dict(nickel_twh=sum(nfc["nonferrous_nickel"].values()) / 1e6, explicit_twh=expl / 1e6, other_twh=(T - expl) / 1e6, other_scale=f, other=oth)
    for case in ("nickel_only_2023", "nf2023_all"):
        d = {k: res[case]["other"][k] - res["main"]["other"][k] for k in res["main"]["other"]}
        rows.append(dict(item=f"option {case}: change against v3 main (2050, TWh)", ni_content_t=float("nan"), electricity_twh=d["electricity"],
                         useful_heat_gt400_twh=d["heat_high"], fuel_input_twh=float("nan"), total_model_twh=res[case]["other_twh"] - res["main"]["other_twh"],
                         source=f"ID nickel {res['main']['nickel_twh']:.3f} -> {res[case]['nickel_twh']:.3f} TWh; other {res['main']['other_twh']:.3f} -> {res[case]['other_twh']:.3f} TWh "
                                f"(scale {res['main']['other_scale']:.6f} -> {res[case]['other_scale']:.6f}); other carriers: " +
                                ", ".join(f"{k} {v:+.3f}" for k, v in d.items() if abs(v) > 1e-9),
                         grade="C", status="PROPOSED (quantified, not implemented)"))
    # ---- product mix and grades ----------------------------------------------------------------------------------------------
    mix = dict(npi_grade_2019=usg["npi_ni"][0] / usg["npi_gross"][0], npi_grade_2023=usg["npi_ni"][-1] / usg["npi_gross"][-1],
               feni_grade_2019=usg["feni_ni"][0] / usg["feni_gross"][0], feni_grade_2023=usg["feni_ni"][-1] / usg["feni_gross"][-1],
               wei_case3_ni_fraction=0.35, share_2019={k: usg[k][0] / sum(usg[x][0] for x in ("npi_ni", "feni_ni", "matte_ni", "mhp_ni")) for k in ("npi_ni", "feni_ni", "matte_ni", "mhp_ni")},
               share_2023={k: usg[k][-1] / sum(usg[x][-1] for x in ("npi_ni", "feni_ni", "matte_ni", "mhp_ni")) for k in ("npi_ni", "feni_ni", "matte_ni", "mhp_ni")},
               ratio_2023_2019_npi=usg["npi_ni"][-1] / usg["npi_ni"][0], ratio_2023_2019_total_v3=q23 / q19, v3_2050_over_2023=led["q_2050_t"] / q23,
               per_t_alloy_scaling_bound=[0.35 / (usg["npi_ni"][-1] / usg["npi_gross"][-1]), 0.35 / (usg["npi_ni"][0] / usg["npi_gross"][0])])
    t = pd.read_csv(R / "industry_v3/NICKEL_ENERGY_WEI2020.csv")
    O = pd.DataFrame(rows); O.to_csv(a.work / "s1/ID_NICKEL_BASEYEAR.csv", index=False, float_format="%.6f")
    ev = dict(unit_energy=ne, wei_rows=t.to_dict("records"), usgs=usg, mix=mix, growth_main=led, growth_nf2023=led23, options=res, T_v2_id_twh=T / 1e6,
              niupper=dict(mwh_per_t_npi_gross=v3.NI_UPPER_MWH_PER_T_NPI, ni_fraction=v3.NI_NPI_NI_FRACTION, implied_mwh_per_t_ni=v3.NI_UPPER_MWH_PER_T_NPI / v3.NI_NPI_NI_FRACTION))
    (a.work / "s1/_nickel_evidence.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 140)
    print(O.drop(columns=["source"]).round(3).to_string()); print(O[O.item.str.startswith("option")].source.to_string())
    print(json.dumps(mix, indent=0, default=float))


if __name__ == "__main__":
    main()
