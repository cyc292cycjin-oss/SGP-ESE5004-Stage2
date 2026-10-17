"""S4C-2 data (decision 83; user decision 2026-10-17 on stop report S4C_STOP_02): national hydro inflow targets and registry fragment s4c_2.

    python scripts_project/s4c_2_data.py --ember <release_generation_yearly_global.csv>

Target per country = median of the Ember yearly hydro generation 2019-2025 (the decision-74 file, CC BY 4.0) x 1.1 (the author multiplier,
pypsa-asean config.default.yaml line 445). Writes research_inputs/hydro_v5/HYDRO_NATIONAL_TARGET_S4C2.csv and
research_inputs/registry_v5/fragments/s4c_2.csv; the diagnosis tables of scripts_project/s4c_2_hydro_diagnosis.py are registered by SHA.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv

SCRIPT = "scripts_project/s4c_2_data.py"
INSTRUCTION_SHA = "e1bad922b036bcb425cb9b77853e5cc4f9ca771c59c90da1a23321b89a1dcdd3"
OUT = ROOT / "research_inputs" / "hydro_v5"
ISO = {"BN": "BRN", "KH": "KHM", "ID": "IDN", "LA": "LAO", "MY": "MYS", "MM": "MMR", "PH": "PHL", "SG": "SGP", "TH": "THA", "TL": "TLS", "VN": "VNM"}
MULTIPLIER = 1.1
EMBER_URL = "https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_yearly_global.csv"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ember", required=True); a = ap.parse_args()
    e = pd.read_csv(a.ember); esha = sha256(a.ember)
    inv = {v: k for k, v in ISO.items()}
    h = e[(e["Electricity source"] == "Hydro") & e["ISO 3 code"].isin(ISO.values()) & e.Year.between(2019, 2025)].copy()
    h["country"] = h["ISO 3 code"].map(inv)
    rows = []
    for c in sorted(ISO):
        x = h[h.country == c].dropna(subset=["Generation (TWh)"]).sort_values("Year")
        if x.empty:
            rows.append(dict(country=c, years="", n_years=0, generation_median_twh=np.nan, target_mwh=np.nan, multiplier=MULTIPLIER, status="NO_EMBER_DATA", series_twh=""))
            continue
        med = float(x["Generation (TWh)"].median())
        rows.append(dict(country=c, years=",".join(str(int(y)) for y in x.Year), n_years=int(len(x)), generation_median_twh=med, target_mwh=med * MULTIPLIER * 1e6, multiplier=MULTIPLIER,
                         status=("REGISTERED" if med > 0 else "SOURCE_ZERO"), series_twh=";".join(f"{int(y)}:{v:g}" for y, v in zip(x.Year, x["Generation (TWh)"]))))
    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["country", "years", "n_years", "generation_median_twh", "multiplier", "target_mwh", "status", "series_twh"]
    write_csv(rows, OUT / "HYDRO_NATIONAL_TARGET_S4C2.csv", cols)
    tsha = sha256(OUT / "HYDRO_NATIONAL_TARGET_S4C2.csv")
    reg = Registry(SCRIPT); cfg = "configs/research/baseline.yaml"
    for r in rows:
        if r["status"] == "REGISTERED":
            reg.add(f"hydro_inflow_target_{r['country']}", f"{r['country']} national annual hydro inflow of the 2050 stock = median Ember hydro generation {r['years']} ({r['generation_median_twh']:.3f} TWh) x {MULTIPLIER} (author multiplier)",
                    r["target_mwh"], "MWh/a", "B", "Ember yearly electricity data (CC BY 4.0) x pypsa-asean config.default.yaml line 445", f"{EMBER_URL}; series {r['series_twh']}", esha, country=r["country"], decision_ref="83")
    reg.add("hydro_inflow_normalization_main", "Decision 83 (user decision 2026-10-17, option B): data correction of the frozen electric base, deviating from the PyPSA-Earth runoff allocation "
            "(build_renewable_profiles.py rescale_hydro: per-unit inflow proportional to upstream runoff). Reason: the author stock is incomplete and the runoff allocation produces physically "
            "impossible unit capacity factors (2.3-4.6), so its spatial shares are not credible; B sets the national hydro total of the stock (author + S4A/S4B additions, reservoir + run-of-river) to "
            "the observed generation x 1.1 and allocates it by capacity share, each unit keeping its own seasonal shape, which also removes the double counting of the added units; new-build reservoir / "
            "run-of-river candidates take the capacity-weighted per-MW inflow of the corrected same-country stock; PHS unaffected", "national_observed", "flag", "B",
            "S4C instruction S4C-2 items 2-4; stop report S4C_STOP_02_HYDRO_DIAGNOSIS.md; user decision 2026-10-17", f"{cfg} research.hydro.inflow_normalization", f"instruction:{INSTRUCTION_SHA}|targets:{tsha}", decision_ref="83")
    reg.add("hydro_inflow_normalization_switch", "research.hydro.inflow_normalization values: national_observed (main, option B: capacity shares) | national_observed_runoff_shares (option A: same national "
            "target, the author runoff shares kept, only the double counting removed; sensitivity) | frozen_base (former state: author inflows and copied inflows of the additions)",
            "national_observed|national_observed_runoff_shares|frozen_base", "flag", "B", "user decision 2026-10-17 item 3", cfg, INSTRUCTION_SHA, decision_ref="83", status="REFERENCE_ONLY")
    reg.add("hydro_inflow_limitation_uniform_cf", "Limitation (option B): within a country every existing hydro unit has the same annual capacity factor (the seasonal shape stays unit by unit); "
            "Ember gives the hydro total only, reservoir and run-of-river are not separated", "limitation", "flag", "B", "user decision 2026-10-17 item 2", "S4C report section S4C-2", INSTRUCTION_SHA,
            decision_ref="83", status="REFERENCE_ONLY")
    reg.add("hydro_smoke_window_artefact", "S4B report section 8 item 12 premise corrected: the ID new-build reservoir proxy CF 1.01-1.08 is the 56-snapshot smoke window (2013-01-01..01-07, wet season) "
            "re-weighted to the year (s2_solve.set_representative_weights); the full-year value is 0.48-0.52", "smoke_artefact", "flag", "B", "scripts_project/s4c_2_hydro_diagnosis.py; S4C_STOP_02 section 3b",
            "results_project/s4c/s4c2", INSTRUCTION_SHA, decision_ref="83", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4c_2.csv")
    print(pd.DataFrame(rows)[["country", "years", "generation_median_twh", "target_mwh", "status"]].to_string())


if __name__ == "__main__":
    main()
