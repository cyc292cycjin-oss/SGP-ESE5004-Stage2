"""S3-7 (user supplement 2026-10-16, item 1): 2040 -> 2050 cost decline of the import supply chains.

The Neumann et al. 2025 import costs (Zenodo 14872184) are 2040 technology assumptions, while the rest of the model uses technology-data
v0.15.0 for 2050. This script compares technology-data v0.15.0 costs_2040.csv and costs_2050.csv (read-only fetched from GitHub) for the main
supply-chain items (solar-utility, onwind, electrolysis, Haber-Bosch, methanolisation, Fischer-Tropsch, H2 liquefaction, H2 (l) storage tank,
H2 (l) transport ship, direct air capture) and estimates the possible import price decline per carrier with cost shares implied by the paper's
Table A.1 sensitivities (arXiv v1 p.15: electrolysis +100 % -> +15.2 %, DAC +100 % -> +25.6 % for the Fischer-Tropsch chain; grade C shares
for the remaining items). The main prices stay the paper values; if the estimate exceeds 20 %, the sensitivity lower bound is widened.

    python scripts_project/s3_7_import_price_decline.py
"""
from __future__ import annotations

import pandas as pd

from d1_common import REG_DIR, ROOT, SRC_DIR, Registry, sha256, write_csv, write_json

SCRIPT = "scripts_project/s3_7_import_price_decline.py"
TD_DIR = SRC_DIR / "technology_data_v0.15.0"
F2040, F2050 = TD_DIR / "technology_data_v0.15.0_costs_2040.csv", TD_DIR / "technology_data_v0.15.0_costs_2050.csv"
URLS = {"2040": "https://raw.githubusercontent.com/PyPSA/technology-data/v0.15.0/outputs/costs_2040.csv", "2050": "https://raw.githubusercontent.com/PyPSA/technology-data/v0.15.0/outputs/costs_2050.csv"}
FETCHED_UTC = "2026-10-15T17:03:42Z"
OUT = ROOT / "research_inputs/imports_v5"
ITEMS = ["solar-utility", "onwind", "electrolysis", "Haber-Bosch", "methanolisation", "Fischer-Tropsch", "H2 liquefaction", "H2 (l) storage tank", "H2 (l) transport ship", "direct air capture", "battery storage"]
# cost shares per chain (fraction of delivered cost); electrolysis and DAC from Table A.1 (+100 % -> +15.2 % / +25.6 %), others grade C assumptions
SHARES = {
    "oil non-fossil": {"res": 0.492, "electrolysis": 0.152, "direct air capture": 0.256, "Fischer-Tropsch": 0.06, "transport": 0.04},
    "methanol": {"res": 0.492, "electrolysis": 0.152, "direct air capture": 0.256, "methanolisation": 0.06, "transport": 0.04},
    "ammonia": {"res": 0.66, "electrolysis": 0.20, "Haber-Bosch": 0.08, "transport": 0.06},
    "hydrogen": {"res": 0.60, "electrolysis": 0.19, "H2 liquefaction": 0.10, "H2 (l) storage tank": 0.05, "H2 (l) transport ship": 0.06},
}
RES_MIX = {"solar-utility": 0.6, "onwind": 0.4}   # exporter RES mix assumption (Western Sahara / Chile: solar-dominated), grade C


def inv(df, tech):
    r = df[(df.technology == tech) & (df.parameter == "investment")]
    return float(r.value.iloc[0]) if len(r) else None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d40, d50 = pd.read_csv(F2040), pd.read_csv(F2050)
    s40, s50 = sha256(F2040), sha256(F2050)
    rows = []
    for t in ITEMS:
        a, b = inv(d40, t), inv(d50, t)
        rows.append(dict(technology=t, investment_2040=a, investment_2050=b, unit=str(d40[(d40.technology == t) & (d40.parameter == "investment")].unit.iloc[0]) if a is not None else "",
                         decline_2040_to_2050=((a - b) / a) if (a and b is not None) else None))
    dec = {r["technology"]: (r["decline_2040_to_2050"] or 0.0) for r in rows}
    res_decline = sum(w * dec[t] for t, w in RES_MIX.items())
    est = []
    for carrier, sh in SHARES.items():
        total = 0.0; parts = {}
        for k, w in sh.items():
            d = res_decline if k == "res" else (0.0 if k == "transport" else dec.get(k, 0.0))
            parts[k] = dict(share=w, decline=d, contribution=w * d); total += w * d
        est.append(dict(carrier=carrier, estimated_decline=total, parts=parts))
    est_df = pd.DataFrame([dict(carrier=e["carrier"], estimated_decline_2040_to_2050=round(e["estimated_decline"], 4), **{f"{k}_share": v["share"] for k, v in e["parts"].items()}, **{f"{k}_decline": round(v["decline"], 4) for k, v in e["parts"].items()}) for e in est])
    write_csv(rows, OUT / "IMPORT_CHAIN_COST_DECLINE_2040_2050.csv", list(rows[0].keys()))
    write_csv(est_df.to_dict("records"), OUT / "IMPORT_PRICE_DECLINE_ESTIMATE_2040_2050.csv", list(est_df.columns))
    max_decline = float(est_df.estimated_decline_2040_to_2050.max())
    low_fraction = max(0.20, round(max_decline, 2))
    reg = Registry(SCRIPT)
    src = "technology-data v0.15.0 outputs/costs_2040.csv and costs_2050.csv (read-only fetch " + FETCHED_UTC + ")"
    for r in rows:
        if r["decline_2040_to_2050"] is not None:
            reg.add("import_chain_decline_" + r["technology"].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").lower(), f"{r['technology']} investment 2040 {r['investment_2040']:.4g} -> 2050 {r['investment_2050']:.4g} {r['unit']}",
                    round(r["decline_2040_to_2050"], 4), "fraction", "B", src, "parameter investment", f"2040:{s40}|2050:{s50}", decision_ref="17", status="REFERENCE_ONLY")
    for e in est:
        reg.add(f"import_price_decline_estimate_{e['carrier'].replace(' ', '_').replace('-', '_')}", f"Estimated 2040 -> 2050 delivered import price decline for {e['carrier']} = sum(share x investment decline); shares: " + ", ".join(f"{k} {v['share']:.3f}" for k, v in e["parts"].items()) +
                " (electrolysis/DAC shares implied by Table A.1 sensitivities, others grade C; RES mix solar 0.6 / onwind 0.4; transport 0 decline); direction: the 2040 base prices are above a 2050 basis, so the applied prices are biased high",
                round(e["estimated_decline"], 4), "fraction", "C", src + " x Neumann et al. Table A.1 implied shares", "arXiv v1 p.15", f"2040:{s40}|2050:{s50}", decision_ref="17", sensitivity_low=0.0, sensitivity_high=round(max(dec.values()), 4))
    reg.add("import_price_sensitivity_low_fraction", f"Lower bound of the import price sensitivity: max(20 %, max estimated 2040->2050 decline {max_decline:.1%}) = {low_fraction:.0%} below the applied price (user supplement 2026-10-16); main prices unchanged",
            low_fraction, "fraction", "C", "s3_7_import_price_decline.py", "IMPORT_PRICE_DECLINE_ESTIMATE_2040_2050.csv", f"2040:{s40}|2050:{s50}", decision_ref="17", sensitivity_low=0.20, sensitivity_high=round(max_decline, 4))
    reg.write(REG_DIR / "fragments" / "import_price_decline.csv")
    write_json(dict(script=SCRIPT, sources=dict(costs_2040=dict(url=URLS["2040"], sha256=s40, fetched_utc=FETCHED_UTC), costs_2050=dict(url=URLS["2050"], sha256=s50, fetched_utc=FETCHED_UTC)), items=rows, res_mix=RES_MIX, res_decline=res_decline,
                    estimates=est, max_decline=max_decline, sensitivity_low_fraction=low_fraction), OUT / "IMPORT_PRICE_DECLINE_EVIDENCE.json")
    pd.set_option("display.width", 220)
    print(pd.DataFrame(rows)[["technology", "investment_2040", "investment_2050", "decline_2040_to_2050"]].round(4).to_string())
    print("RES decline (0.6 solar / 0.4 onwind):", round(res_decline, 4)); print(est_df[["carrier", "estimated_decline_2040_to_2050"]].to_string()); print("max", round(max_decline, 4), "-> sensitivity low fraction", low_fraction)


if __name__ == "__main__":
    main()
