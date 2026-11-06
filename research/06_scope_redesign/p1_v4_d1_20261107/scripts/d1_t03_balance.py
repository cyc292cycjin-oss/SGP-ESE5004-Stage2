"""V4 D1 section 5 (decision 214 (a); T03): palm oil mill energy balance and the in-mill self-use shares of mesocarp fibre and palm kernel shell (PKS).

    PYTHONHASHSEED=0 <env python> scripts/d1_t03_balance.py <repo> <delivery dir> <faostat csv>

Inputs (read only): the literature evidence evidence/T03_LITERATURE.json (ids T03-*; URLs, access UTC, short quotes, pages), the v3.1 potential table
research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv (the FFB 2050 base of the v4 potential = fibre mass / (0.144 x 0.9)) and the FAOSTAT QCL extraction
(check only). Writes PALM_MILL_ENERGY_BALANCE.csv, PALM_MILL_SELF_USE.csv (delivery and research_inputs/biomass_v5/), evidence/T03_BALANCE.json.

Energy balance (instruction 5.2; per t FFB): fuel heat Q = steam x enthalpy rise / boiler efficiency (back-pressure turbine on the same steam: the mill
electricity is inside the boiler steam, no extra fuel); available heat fibre A_f = x_f x LHV_f, shell A_s = x_s x LHV_s (as received); fibre first, PKS fills:
share_f = min(1, Q / A_f), share_s = min(1, max(0, (Q - A_f) / A_s)).
Central-value rule (fixed before computing): each parameter = median over independent source groups (one value per group); MAIN = pooled per-tonne
parameters for every country (no parameter has three or more country-specific groups); VARIANT B = country-specific medians where a country has >= 2 groups
(mass fractions MY / ID / TH, steam TH), pooled otherwise. Literature shares per country = median over independent groups of that country (KH, PH: no country
source -> pooled over all groups). POEB 103 (Yap & Menon 2012) is not a literature share: its 15 % / 22 % are computed from the mill electricity with an
isentropic Rankine efficiency and no boiler efficiency (T03-A02, T03-I01), not observed.
Decision rule (instruction 5.3, registered by the instruction): literature vs balance |difference| <= 0.15 and their mean within 0.15 of the current value
(fibre 1.00, PKS 0.50) -> keep, grade up, register the range; consistent but > 0.15 from the current value -> replace by the mean of the two centres;
literature vs balance > 0.15 -> contradictory: keep, report. Low / high in every case.
"""
import hashlib
import json
import statistics as st
import sys
from pathlib import Path

import pandas as pd

REPO, OUT, FAO = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
EV = json.loads((OUT / "evidence/T03_LITERATURE.json").read_text(encoding="utf-8"))
IDS = {e["id"] for e in EV}
CURRENT = dict(fibre=1.00, pks=0.50)
TOL = 0.15
COUNTRIES = ["ID", "MY", "TH", "PH", "KH"]

# ---- per-tonne parameters: (value, evidence id, independent group, country or "", note); one value per group ---------------------------------------------
P = dict(
    steam_t_per_t=[(0.54, "T03-D01", "G02", "MY", "Vijaya 2008, 12 mills, mean (0.45-0.75)"), (0.56, "T03-D02", "G12", "TH", "Chavalparit 2006 Factory A"),
                   (0.60, "T03-D03", "G08", "ID", "Yusniati 2018 design"), (0.49, "T03-D04", "G11", "TH", "Huailuek 2019 surveyed mills"),
                   (0.665, "T03-D06", "G03", "", "Nasrin 2011 / BPPT 2016 via HRO 0.6-0.73 (mid; country not attributable)")],
    dh_gj_per_t=[(2.60, "T03-D03", "G08", "ID", "Yusniati: 20 kg/cm2, 280 C, feed 90 C, rise 620.87 kcal/kg"),
                 (2.667, "T03-D07", "G01", "MY", "POEB 103: h1 2801 kJ/kg (21 barg) - feed water 32 C (134 kJ/kg, steam table, INFERENCE)"),
                 (2.659, "T03-D21", "G19", "MY", "POEB 116: feed water about 34 C (142 kJ/kg) to 20 bar saturated steam (h about 2,801 kJ/kg; steam table, INFERENCE)")],
    boiler_eff=[(0.73, "T03-D19", "G08", "ID", "Yusniati specification"), (0.775, "T03-D20", "G03", "", "Nasrin 2011 via HRO 71-84 % (mid)")],
    x_fibre=[(0.13, "T03-D08", "G01", "MY", "POEB 103 (MPOB pocketbook 2010)"), (0.121, "T03-D09", "G02", "MY", "Vijaya 2008 12 mills"),
             (0.15, "T03-D10", "G07", "ID", "GIZ 2014 / IOPRI 2012"), (0.126, "T03-D11", "G11", "TH", "Huailuek 2019 surveyed mills"),
             (0.13, "T03-D13", "G08", "ID", "Yusniati 2018 12-14 % (mid)"), (0.14, "T03-B12", "G12", "TH", "Chavalparit 2006 Factory A 140 kg/t"),
             (0.125, "T03-D12", "G10", "", "HRO 2018 compilation of 7 sources (median 12.5 %)")],
    x_shell=[(0.06, "T03-D08", "G01", "MY", "POEB 103"), (0.070, "T03-D09", "G02", "MY", "Vijaya 2008"), (0.065, "T03-D10", "G07", "ID", "GIZ 2014"),
             (0.041, "T03-D11", "G11", "TH", "Huailuek 2019 surveyed mills"), (0.07, "T03-D13", "G08", "ID", "Yusniati 6-8 % (mid)"),
             (0.055, "T03-B12", "G12", "TH", "Chavalparit 2006 55 kg/t"), (0.064, "T03-D12", "G10", "", "HRO 2018 compilation (median 6.4 %)")],
    lhv_fibre=[(13.054, "T03-D14", "G01", "MY", "37 % moisture"), (9.65, "T03-D15", "G08", "ID", "39.8 % moisture"), (11.3, "T03-D16", "G20", "", "Mahlia 2001 NCV"),
               (11.48, "T03-D17", "G21", "", "Fauzianto 2014")],
    lhv_shell=[(18.418, "T03-D14", "G01", "MY", "12 % moisture"), (14.57, "T03-D15", "G08", "ID", "23.5 % moisture"), (17.5, "T03-D16", "G20", "", "Mahlia 2001 NCV"),
               (14.55, "T03-D17", "G21", "", "Fauzianto 2014")],
)
RANGE = dict(steam_t_per_t=(0.45, 0.75, "T03-D01 mill range"), dh_gj_per_t=(2.196, 2.835, "POEB 103 calc 605 kJ/kg feed; 280 C from 34 C (steam table, INFERENCE)"),
             boiler_eff=(0.71, 0.85, "T03-D20 low, T03-D22 optimum"), x_fibre=(0.106, 0.15, "T03-D12 / T03-D10"), x_shell=(0.041, 0.08, "T03-D11 / T03-D13"),
             lhv_fibre=(9.65, 13.054, "T03-D15 / T03-D14"), lhv_shell=(14.55, 18.418, "T03-D17 / T03-D14"))
# ---- observed in-mill shares (literature), one value per independent group -----------------------------------------------------------------------------------
LIT = dict(fibre=[(0.865, "T03-B01", "G02", "MY", "Vijaya 2008, 12 mills, aggregate (median 0.858; 0.746-1.0)"),
                  (0.805, "T03-B03", "G03", "MY", "Nasrin 2011 via HRO, 6 mills mean (0.73-0.90)"),
                  (0.95, "T03-B04", "G04", "MY", "Aghamohammadi 2016 via HRO, Sarawak"),
                  (1.00, "T03-B08", "G08", "ID", "Yusniati 2018, one mill (engineering calculation)"),
                  (0.85, "T03-B09", "G09", "ID", "Setiadi 2014 via HRO"),
                  (0.993, "T03-B11", "G11", "TH", "Huailuek 2019, 748 / 753 kg"),
                  (0.964, "T03-B12", "G12", "TH", "Chavalparit 2006 Factory A, 135 / 140 kg")],
           pks=[(0.452, "T03-B01", "G02", "MY", "Vijaya 2008, 12 mills, aggregate (median 0.368; 0.184-1.0)"),
                (0.58, "T03-B03", "G03", "MY", "Nasrin 2011 via HRO, 6 mills mean (0.10-0.80)"),
                (0.50, "T03-B04", "G04", "MY", "Aghamohammadi 2016 via HRO"),
                (0.50, "T03-B05", "G05", "MY", "Dit 2007 via HRO"),
                (0.50, "T03-B07", "G07", "ID", "IOPRI 2012 via GIZ 2014: 84 % of 21 mills burn >= 50 % (lower bound read as 0.50, INFERENCE)"),
                (0.63, "T03-B08", "G08", "ID", "Yusniati 2018, one mill"),
                (0.55, "T03-B09", "G09", "ID", "Setiadi 2014 via HRO"),
                (0.048, "T03-B11", "G11", "TH", "Huailuek 2019, 12 / 248 kg"),
                (0.545, "T03-B12", "G12", "TH", "Chavalparit 2006 Factory A, 30 / 55 kg (same book also writes 20 %, T03-I04)")])
for k, rows in list(P.items()) + list(LIT.items()):
    for r in rows:
        assert r[1] in IDS, (k, r[1])


def med(rows, cc=None):
    v = [r[0] for r in rows if cc is None or r[3] == cc]
    return st.median(v) if v else None


def groups(rows, cc=None):
    return len({r[2] for r in rows if cc is None or r[3] == cc})


pooled = {k: med(v) for k, v in P.items()}


def params(cc, variant):
    q = dict(pooled)
    if variant == "B":
        for k, rows in P.items():
            if groups(rows, cc) >= 2:
                q[k] = med(rows, cc)
    return q


def balance(q):
    Q = q["steam_t_per_t"] * q["dh_gj_per_t"] / q["boiler_eff"]
    af, ash = q["x_fibre"] * q["lhv_fibre"], q["x_shell"] * q["lhv_shell"]
    sf = min(1.0, Q / af); ss = min(1.0, max(0.0, (Q - af) / ash))
    return dict(Q_gj_per_t_ffb=Q, A_fibre_gj=af, A_shell_gj=ash, share_fibre=sf, share_pks=ss)


def extreme(low_share: bool):
    """parameter corner giving the lowest (highest) shares: less (more) steam, enthalpy, fuel need; more (less) fuel available"""
    q = {}
    for k, (lo, hi, _) in RANGE.items():
        need = k in ("steam_t_per_t", "dh_gj_per_t")
        q[k] = (lo if need else hi) if low_share else (hi if need else lo)
        if k == "boiler_eff":
            q[k] = hi if low_share else lo
    return balance(q)


# ---- FFB base of the v4 potential (2050) and FAOSTAT check --------------------------------------------------------------------------------------------------
bp = pd.read_csv(REPO / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv", keep_default_na=False)
fb = bp[bp.category == "oil_palm_fibre"].set_index("country")
pk = bp[bp.category == "oil_palm_pks"].set_index("country")
ffb2050 = {cc: float(fb.at[cc, "mass_main_t"]) / (0.144 * 0.9) for cc in COUNTRIES}
fao = pd.read_csv(FAO)
fao = fao[(fao.Item == "Oil palm fruit") & (fao.Element == "Production") & fao.Year.between(2019, 2023)]
iso = {"Indonesia": "ID", "Malaysia": "MY", "Thailand": "TH", "Philippines": "PH", "Cambodia": "KH"}
fao_mean = {iso[a]: float(g.Value.mean()) for a, g in fao.groupby("Area") if a in iso}
GROWTH = 1.011 ** 9 * 1.003 ** 20   # d1_biomass.GROWTH_2021_2050

rows, sel, verdicts = [], [], {}
bal_main = balance(params(None, "A"))
lo_corner, hi_corner = extreme(True), extreme(False)
for cc in COUNTRIES:
    bA = balance(params(cc, "A")); bB = balance(params(cc, "B"))
    rec = dict(country=cc, ffb_2050_t=ffb2050[cc], ffb_2019_2023_mean_t_faostat=fao_mean.get(cc), ffb_2050_check_ratio=(ffb2050[cc] / (fao_mean[cc] * GROWTH)) if cc in fao_mean else None)
    out = {}
    for s in ("fibre", "pks"):
        own = groups(LIT[s], cc) >= 1
        lit = med(LIT[s], cc) if own else med(LIT[s])
        litv = [r[0] for r in LIT[s] if (r[3] == cc or not own)]
        b = bA[f"share_{s}"]; bb = bB[f"share_{s}"]
        consistent = abs(lit - b) <= TOL
        mean = (lit + b) / 2
        if not consistent:
            verdict, mid = "CONTRADICTORY: keep the current value, report (instruction 5.3 c)", CURRENT[s]
        elif abs(mean - CURRENT[s]) <= TOL:
            verdict, mid = "CONSISTENT, within 0.15 of the current value: keep, grade up, register the range (5.3 a)", CURRENT[s]
        else:
            verdict, mid = "CONSISTENT, > 0.15 from the current value: replace by the mean of the two centres (5.3 b)", mean
        lo = max(0.0, min(litv + [b, bb])); hi = min(1.0, max(litv + [b, bb]))
        lo, hi = min(lo, mid), max(hi, mid)
        verdicts[(cc, s)] = verdict
        out[s] = dict(lit=lit, lit_groups=groups(LIT[s], cc) if own else groups(LIT[s]), lit_basis=("country" if own else "pooled (no country source)"),
                      bal_A=b, bal_B=bb, diff_A=lit - b, diff_B=lit - bb, consistent_A=consistent, consistent_B=abs(lit - bb) <= TOL, mean=mean, verdict=verdict,
                      low=lo, mid=mid, high=hi, sources=";".join(r[1] for r in LIT[s] if (r[3] == cc or not own)))
    Q = bA["Q_gj_per_t_ffb"]
    pot_f, pot_s = float(fb.at[cc, "potential_main_mwh"]), float(pk.at[cc, "potential_main_mwh"])
    rec.update(Q_gj_per_t_ffb=Q, fuel_need_2050_TWh=ffb2050[cc] * Q / 3.6 / 1e6,
               fibre_available_2050_TWh_asreceived=ffb2050[cc] * bA["A_fibre_gj"] / 3.6 / 1e6, shell_available_2050_TWh_asreceived=ffb2050[cc] * bA["A_shell_gj"] / 3.6 / 1e6,
               potential_fibre_v3_TWh=pot_f / 1e6, potential_pks_v3_TWh=pot_s / 1e6, potential_lhv_gj_t=float(fb.at[cc, "lhv_gj_per_t"]),
               **{f"{s}_{k}": v for s in out for k, v in out[s].items()},
               variant_B_params=json.dumps({k: round(v, 6) for k, v in params(cc, "B").items()}))
    rows.append(rec)
    grade = dict(fibre=("B" if cc == "MY" else "C"), pks=("C" if out["pks"]["consistent_A"] else "D"))
    sel.append(dict(country=cc, fibre_low=round(out["fibre"]["low"], 4), fibre_mid=out["fibre"]["mid"], fibre_high=round(out["fibre"]["high"], 4),
                    pks_low=round(out["pks"]["low"], 4), pks_mid=out["pks"]["mid"], pks_high=round(out["pks"]["high"], 4),
                    grade_fibre=grade["fibre"], grade_pks=grade["pks"],
                    verdict_fibre=out["fibre"]["verdict"].split(":")[0].split(",")[0], verdict_pks=out["pks"]["verdict"].split(":")[0].split(",")[0],
                    literature_fibre=round(out["fibre"]["lit"], 4), literature_pks=round(out["pks"]["lit"], 4),
                    balance_fibre=round(out["fibre"]["bal_A"], 4), balance_pks=round(out["pks"]["bal_A"], 4),
                    sources_fibre=out["fibre"]["sources"], sources_pks=out["pks"]["sources"],
                    rule="V4 D1 T03 (instruction 5.3): mid = current value unless literature and energy balance agree within 0.15 and their mean differs from it by > 0.15; "
                         "low / high = min / max of the independent literature values and the two balance variants",
                    status="VERIFIED (literature) / INFERENCE (energy balance)"))
bal = pd.DataFrame(rows)
bal.to_csv(OUT / "PALM_MILL_ENERGY_BALANCE.csv", index=False, float_format="%.6f", lineterminator="\n")
tab = pd.DataFrame(sel)
tab.to_csv(OUT / "PALM_MILL_SELF_USE.csv", index=False, lineterminator="\n")
tab.to_csv(REPO / "research_inputs/biomass_v5/PALM_MILL_SELF_USE.csv", index=False, lineterminator="\n")
# ---- low / high effects on the v4 potential (no file written; central unchanged when mid = current) ------------------------------------------------------------
eff = []
for r in tab.itertuples():
    pf, ps = float(fb.at[r.country, "potential_main_mwh"]) / 1e6, float(pk.at[r.country, "potential_main_mwh"]) / 1e6
    for lev in ("low", "mid", "high"):
        f, s = getattr(r, f"fibre_{lev}"), getattr(r, f"pks_{lev}")
        eff.append(dict(country=r.country, level=lev, fibre_share=f, pks_share=s, d_potential_vs_current_TWh=-(f - CURRENT["fibre"]) * pf - (s - CURRENT["pks"]) * ps))
eff = pd.DataFrame(eff)
# ---- PKS leaving the mills (side evidence, instruction 5.1): exports / Japanese imports vs PKS generated (FAOSTAT 2019-2023 FFB x pooled shell fraction) ----
gen = {cc: fao_mean[cc] * pooled["x_shell"] for cc in ("ID", "MY")}
trade = [dict(item="ID exports 2020 Q1 x 4 (T03-C01, annualised: INFERENCE)", country="ID", t_per_a=702e3 * 4),
         dict(item="MY exports 2020 Q1 x 4 (T03-C01, annualised: INFERENCE)", country="MY", t_per_a=204e3 * 4),
         dict(item="Japan imports from ID 2025-03 x 12 (T03-C02, annualised: INFERENCE)", country="ID", t_per_a=477.7e3 * 12),
         dict(item="Japan imports from MY 2025-03 x 12 (T03-C02, annualised: INFERENCE)", country="MY", t_per_a=187.5e3 * 12)]
for t in trade:
    t["pks_generated_t_per_a"] = gen[t["country"]]; t["share_leaving_mills_lower_bound"] = t["t_per_a"] / gen[t["country"]]
json.dump(dict(pks_trade_side_evidence=trade, pks_generated_2019_2023_t=gen,
               pooled_params=pooled, groups={k: groups(v) for k, v in P.items()}, balance_main=bal_main, balance_low_corner=lo_corner, balance_high_corner=hi_corner,
               ranges=RANGE, current=CURRENT, tolerance=TOL, verdicts={f"{a}_{b}": v for (a, b), v in verdicts.items()},
               potential_effect_TWh=eff.to_dict("records"), asean_effect_TWh={lev: float(eff[eff.level == lev].d_potential_vs_current_TWh.sum()) for lev in ("low", "mid", "high")},
               literature=LIT, parameters=P, evidence_sha256=hashlib.sha256((OUT / "evidence/T03_LITERATURE.json").read_bytes()).hexdigest(),
               table_sha256=hashlib.sha256((OUT / "PALM_MILL_SELF_USE.csv").read_bytes()).hexdigest()),
          open(OUT / "evidence/T03_BALANCE.json", "w"), indent=1, default=float, ensure_ascii=False)
print("pooled", {k: round(v, 4) for k, v in pooled.items()}); print("balance main", {k: round(v, 4) for k, v in bal_main.items()})
print("corners low", {k: round(v, 3) for k, v in lo_corner.items()}, "high", {k: round(v, 3) for k, v in hi_corner.items()})
print(bal[["country", "ffb_2050_t", "ffb_2050_check_ratio", "fuel_need_2050_TWh", "fibre_lit", "fibre_bal_A", "pks_lit", "pks_bal_A", "pks_bal_B", "pks_diff_A", "pks_diff_B"]].round(4).to_string(index=False))
print(tab[["country", "fibre_low", "fibre_mid", "fibre_high", "pks_low", "pks_mid", "pks_high", "grade_fibre", "grade_pks", "verdict_fibre", "verdict_pks"]].to_string(index=False))
print(eff.pivot(index="country", columns="level", values="d_potential_vs_current_TWh").round(3).to_string())
print(pd.DataFrame(trade).round(3).to_string(index=False))
