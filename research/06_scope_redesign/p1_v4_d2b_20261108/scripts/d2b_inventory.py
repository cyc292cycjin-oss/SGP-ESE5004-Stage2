"""V4 D2b section 7: input inventory of the rerank = the W10 C-grade inventory with the D2b overrides of rows whose notch is NOT a registered sensitivity
range (the rerank's --registry-ranges refreshes the registered-range rows from this branch's registry by itself). No solver.

    python scripts/d2b_inventory.py <W10 C_GRADE_INVENTORY.csv> <out csv>

Overrides (D2b evidence):
  offwind_alpha_calibration_rule  relative alpha notch -13.0 % / +23.8 % (onshore proxy) -> VN reference-area coefficient range under the S4B-3 rule
                                  0.849 / 1.042 relative to alpha 1.0 = -15.08 % / +4.23 % (evidence/VN_OFFWIND_ALPHA.json; registry v4_offwind_alpha_vn_reference_area)
  co2_sequestration_cost_price_year  factor 0.86-1.0 (by analogy) -> 0.952-1.0 (price year 2015-2020, euro-area HICP 100 / 105.06; registry value 2020, INFERENCE)
"""
import json
import sys
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]


def main():
    inv = pd.read_csv(sys.argv[1], dtype=str, keep_default_na=False)
    a = json.loads((W / "evidence/VN_OFFWIND_ALPHA.json").read_text())["alpha_cf_match"]
    lo, hi = a["pecc3_binh_thuan_net"]["alpha_box"] - 1.0, a["wb_roadmap_2050_net"]["alpha_box"] - 1.0
    ov = {"offwind_alpha_calibration_rule": (lo, hi, f"D2b 4.6: VN reference-area coefficient range under the S4B-3 rule (Binh Thuan, ERA5 2013, model turbine x 0.8855): alpha {1 + lo:.3f}-{1 + hi:.3f} relative to 1.0; replaces the onshore proxy -13.0 % / +23.8 %"),
          "co2_sequestration_cost_price_year": (100.0 / 105.06, 1.0, "D2b 4.3: price year 2020 inferred (release commit e43746df with technology-data v0.13.2, eur_year 2020); range 2015-2020 -> factor 0.952-1.0 (euro-area HICP)")}
    log = []
    for pid, (l, h, why) in ov.items():
        m = inv.param_id == pid
        if m.sum() != 1:
            raise SystemExit(f"{pid}: {m.sum()} inventory rows")
        i = inv.index[m][0]
        log.append(dict(param_id=pid, notch_low_w10=inv.at[i, "notch_low"], notch_high_w10=inv.at[i, "notch_high"], notch_low_d2b=repr(l), notch_high_d2b=repr(h), basis=why))
        inv.at[i, "notch_low"] = repr(l); inv.at[i, "notch_high"] = repr(h); inv.at[i, "notch_basis"] = why
    inv.to_csv(sys.argv[2], index=False, lineterminator="\n")
    pd.DataFrame(log).to_csv(Path(sys.argv[2]).with_name("INVENTORY_OVERRIDES_D2B.csv"), index=False, lineterminator="\n")
    print(pd.DataFrame(log)[["param_id", "notch_low_w10", "notch_high_w10", "notch_low_d2b", "notch_high_d2b"]].to_string())


if __name__ == "__main__":
    main()
