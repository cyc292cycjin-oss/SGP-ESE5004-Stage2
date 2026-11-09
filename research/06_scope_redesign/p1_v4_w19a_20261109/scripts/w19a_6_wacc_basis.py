"""W19a section 3: WACC basis unification table (read only; no model change).

Inputs: work/p1_step4r_20261020/COUNTRY_WACC_SENSITIVITY_TABLE.csv (IEA nominal post-tax midpoints / MY reference + Damodaran CRP,
IMF WEO Oct 2026 CPI 2028-2030 average; = COUNTRY_WACC_REAL_M08A.csv real_wacc_mid). Statutory corporate income tax rates are
INFERENCE (from memory, to be verified against PwC Worldwide Tax Summaries / national tax authorities; one web search 2026-11-08
returned sources of mixed vintage).

Formulas (EXACT given the inputs):
  real post-tax  r_rp = (1 + n) / (1 + pi) - 1                       (the current table)
  nominal pre-tax n_pre = n / (1 - tau)                               (exact for WACC_post = E/V r_E + D/V r_D (1 - tau),
                                                                       WACC_pre = E/V r_E / (1 - tau) + D/V r_D)
  real pre-tax   r_rpre = (1 + n / (1 - tau)) / (1 + pi) - 1
"""
import csv
import json
from pathlib import Path

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109")
SRC = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4r_20261020/COUNTRY_WACC_SENSITIVITY_TABLE.csv")
TAX = {"BN": 0.185, "KH": 0.20, "ID": 0.22, "LA": 0.20, "MY": 0.24, "MM": 0.22, "PH": 0.25, "SG": 0.17, "TH": 0.20, "TL": 0.10, "VN": 0.20}  # INFERENCE
UNIFORM = 0.07


def main():
    rows, out = list(csv.DictReader(open(SRC, encoding="utf-8"))), []
    for r in rows:
        c = r["country"]
        if not r["nominal_wacc_mid"]:
            continue
        pi, tau = float(r["imf_inflation_2028_2030_avg"]), TAX[c]
        rec = dict(country=c, method=r["method"], inflation_pi=pi, tax_tau_INFERENCE=tau)
        for k in ("low", "mid", "high"):
            n = float(r[f"nominal_wacc_{k}"])
            rec[f"nominal_post_{k}"] = n
            rec[f"real_post_{k}"] = (1 + n) / (1 + pi) - 1
            rec[f"nominal_pre_{k}"] = n / (1 - tau)
            rec[f"real_pre_{k}"] = (1 + n / (1 - tau)) / (1 + pi) - 1
        for dt in (-0.05, 0.05):
            t2 = min(max(tau + dt, 0.0), 0.5)
            rec[f"real_pre_mid_tau{'+' if dt > 0 else '-'}5pp"] = (1 + float(r["nominal_wacc_mid"]) / (1 - t2)) / (1 + pi) - 1
        rec["table_real_wacc_mid"] = float(r["real_wacc_mid"])
        rec["check_table_equals_formula"] = abs(rec["real_post_mid"] - rec["table_real_wacc_mid"]) < 1e-4
        out.append(rec)
    # TL rule: mean of KH / LA / MM (decision 133) on each basis
    tl = {k: sum(o[k] for o in out if o["country"] in ("KH", "LA", "MM")) / 3 for k in out[0] if k.startswith(("real_", "nominal_"))}
    out.append(dict(country="TL", method="rule: mean of KH / LA / MM (decision 133)", inflation_pi="", tax_tau_INFERENCE=TAX["TL"], **tl, table_real_wacc_mid=0.092367,
                    check_table_equals_formula=abs(tl["real_post_mid"] - 0.092367) < 1e-4))
    keys = list(out[0].keys())
    with open(D / "evidence" / "WACC_BASIS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow({k: o.get(k, "") for k in keys}) for o in out]
    summ = {}
    for basis in ("real_post_mid", "real_pre_mid", "real_pre_mid_tau-5pp", "real_pre_mid_tau+5pp", "nominal_post_mid", "nominal_pre_mid"):
        v = [o[basis] for o in out]
        summ[basis] = dict(min=min(v), max=max(v), min_country=out[v.index(min(v))]["country"], max_country=out[v.index(max(v))]["country"],
                           uniform_inside=min(v) <= UNIFORM <= max(v), countries_above_7pct=sorted(o["country"] for o in out if o[basis] > UNIFORM),
                           unweighted_mean=sum(v) / len(v))
    # the uniform 7 % read on its documented origin (Noothout 2016 EU onshore wind, nominal post-tax) -> real bases for an EU-type pi = 2 %, tau = 25 % (INFERENCE)
    alt = dict(as_real_pre="7.00 % (reading 1: no tax and constant prices in the LP)",
               origin_nominal_post_to_real_post=(1.07 / 1.02 - 1), origin_nominal_post_to_real_pre_tau25=((1 + 0.07 / 0.75) / 1.02 - 1))
    res = dict(summary=summ, uniform_alternative_readings=alt, tax_rates_INFERENCE=TAX, all_tables_formula_check=all(o["check_table_equals_formula"] for o in out))
    (D / "evidence" / "WACC_BASIS.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))
    for o in out:
        print(o["country"], f"post {o['real_post_mid']:.4f}  pre {o['real_pre_mid']:.4f}  (tau-5 {o['real_pre_mid_tau-5pp']:.4f}, tau+5 {o['real_pre_mid_tau+5pp']:.4f})  table {o['table_real_wacc_mid']:.4f} ok={o['check_table_equals_formula']}")


if __name__ == "__main__":
    main()
