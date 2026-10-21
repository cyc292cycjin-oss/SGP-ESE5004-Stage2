"""M08a (decisions 129-133): registry rows of the implementation step (no build, no solve).

    python scripts_project/m08a_data.py      # then python scripts_project/d1_registry.py

Writes research_inputs/registry_v5/fragments/m08a.csv (new rows) and fragments/m08a_corrections.csv (full-row
replacements of existing param_ids, applied by d1_registry.py after m080_corrections). A superseded row keeps its
value, gets status REFERENCE_ONLY and the description suffix " | [M08a] 历史：已被 <new id> 替代 ..."; the rows to
replace are taken from the assembly of all other fragments (+ the M08-0 corrections), never from an earlier M08a
output, so re-running gives the same files. One function per instruction task (A2 ...); rows of A1 are written by
scripts_project/s2_0_cost_layer_v015.py (the script that computes them).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from d1_common import COLUMNS, REG_DIR, ROOT, Registry, sha256, write_csv   # noqa: E402
from s2_costs import AEO8_PDF_SHA, D15_FILE, smr_ratios   # noqa: E402

SCRIPT = "scripts_project/m08a_data.py"
STEP = "M08a"
D15 = ROOT / D15_FILE


class Corrections:
    """Full-row replacements built from the registry assembled WITHOUT the M08a fragments (deterministic re-runs)."""

    def __init__(self):
        import d1_registry
        frames = [pd.read_csv(REG_DIR / "fragments" / f"{f}.csv", dtype=str, keep_default_na=False)
                  for f in d1_registry.FRAGMENTS if not f.startswith("m08a")]
        u = Registry("scripts_project/d1_registry.py"); d1_registry.unit_rows(u)
        frames.append(pd.DataFrame(u.rows, columns=COLUMNS))
        df = pd.concat(frames, ignore_index=True)[COLUMNS]
        for f in d1_registry.CORRECTIONS:
            if f.startswith("m08a"):
                continue
            corr = pd.read_csv(REG_DIR / "fragments" / f"{f}.csv", dtype=str, keep_default_na=False)[COLUMNS]
            df = pd.concat([df[~df.param_id.isin(corr.param_id)], corr], ignore_index=True)
        self.base = df.set_index("param_id")
        self.rows = {}

    def supersede(self, pid: str, by: str, step: str, note: str = "", status: str = "REFERENCE_ONLY", **changes):
        if pid in self.rows:
            raise ValueError(f"{pid} superseded twice")
        r = self.base.loc[pid].to_dict()
        r.update({k: ("" if v is None else str(v)) for k, v in changes.items()})
        r["description"] = f"{r['description']} | [{STEP} {step}] 历史：已被 {by} 替代" + (f" ({note})" if note else "")
        r["status"] = status
        refs = [x.strip() for x in str(r.get("decision_ref", "")).replace(";", ",").split(",") if x.strip()]
        r["decision_ref"] = ", ".join(refs + [x for x in ("131",) if x not in refs])
        r["param_id"] = pid
        self.rows[pid] = r

    def value(self, pid: str) -> str:
        return self.base.loc[pid, "value"]


# --- A2 (M08-2, decision 131): nuclear from one source; AEO8 price-year factor -----------------------------------
def a2(reg: Registry, cor: Corrections):
    q = smr_ratios(D15)
    src_d15 = f"AEO8 pdf:{AEO8_PDF_SHA}; D15:{sha256(D15)}"
    reg.add("nuclear_cost_rule", "R6.3 / M08-2 (decision 131): one source for large PWR and SMR = technology-data v0.15.0 'nuclear' (EUR2020 main layer, PyPSA-Eur practice); "
            "SMR = nuclear x AEO8 Table D.15 same-table ratios SMR / LWR: investment 9,600 / 9,000 = 1.0667, FOM share of investment (110.0 / 9,600) / (75.3 / 9,000) = 1.37, "
            "VOM 2.2 / 5.1 = 0.43; lifetime, efficiency, fuel (uranium) and discount rate = technology-data nuclear; ratios are currency-year neutral; INL/ATB 2024 "
            "(USD2022: SMR moderate 2050 4,000, large 3,750 USD/kW) is the registered sensitivity set; config research.cost_layer.smr_cost_source = td_nuclear_x_aeo8_ratio "
            "(main) | aeo8_author_rule_2050 (former: AEO8 D.15 SMR x ECB 2020 FX, registry smr_*)",
            "td_nuclear_x_aeo8_ratio", "rule", "C", "technology-data v0.15.0 nuclear (Lazard v16.0); AEO8 Table D.15 p.197; INL/RPT-24-77048 Rev.2 Table A-1",
            "scripts_project/s2_costs.py smr_rows; AEO8_Table_D15_Cost_Summary.csv rows Nuclear LWR / Nuclear SMR", src_d15, decision_ref="126, 46, 131")
    for k, v, d in [("investment", q["investment"], "investment SMR / LWR = 9,600 / 9,000 kUSD/MW"),
                    ("fom_share", q["fom_share"], "FOM share of investment SMR / LWR = (110.0 / 9,600) / (75.3 / 9,000); applied to the technology-data nuclear FOM in %/a"),
                    ("vom", q["vom"], "VOM SMR / LWR = 2.2 / 5.1 USD/MWh; applied to the technology-data nuclear VOM")]:
        reg.add(f"smr_ratio_aeo8_{k}", f"M08-2 (decision 131): AEO8 Table D.15 same-table ratio for the SMR rule nuclear_cost_rule - {d}", v, "ratio", "B",
                "ACE AEO8 (2024) Appendix D Table D.15 p.197", "AEO8_Table_D15_Cost_Summary.csv", src_d15, decision_ref="131", sensitivity_low=None, sensitivity_high=None)
    reg.add("aeo8_cost_price_year", "R6.2 / M08-2 (decision 131): the AEO8 Table D.15 price year is not stated (Appendix D.3 p.195) -> DATA_PENDING; treatment = sensitivity factor "
            "research.cost_layer.aeo8_price_year_factor in [0.86, 1.00] on the AEO8 EUR2020 values (main 1.0; 0.86 = USD2023 -> USD2020 by FRED A191RD3A086NBEA 0.887 rounded "
            "down for USD2022-23); applied to the geothermal new-build investment (and to the SMR investment / VOM only under the former smr_cost_source aeo8_author_rule_2050; "
            "the main SMR rule uses currency-neutral ratios)", "DATA_PENDING", "year", "C", "ACE AEO8 (2024) Appendix D.3 p.195", "Appendix D", src_d15,
            decision_ref="126, 131", status="DATA_PENDING")
    reg.add("aeo8_price_year_factor_main", "M08-2 (decision 131): research.cost_layer.aeo8_price_year_factor main value 1.0 (AEO8 values used as EUR2020 after ECB 2020 FX); "
            "sensitivity 0.86 (registry aeo8_cost_price_year)", 1.0, "factor", "C", "configs/research/baseline.yaml research.cost_layer.aeo8_price_year_factor",
            "aeo8_price_year_factor", sha256(ROOT / "configs/research/baseline.yaml"), decision_ref="131", sensitivity_low=0.86, sensitivity_high=1.0)
    for pid in ("smr_investment", "smr_FOM", "smr_VOM"):
        cor.supersede(pid, "nuclear_cost_rule", "A2", "kept for the former option smr_cost_source = aeo8_author_rule_2050")


def main(steps=("a2",)):
    reg = Registry(SCRIPT); cor = Corrections()
    for s in steps:
        globals()[s](reg, cor)
    out = REG_DIR / "fragments"
    reg.write(out / "m08a.csv")
    rows = [cor.rows[k] for k in sorted(cor.rows)]
    write_csv(rows, out / "m08a_corrections.csv", COLUMNS)
    print(f"m08a.csv {len(reg.rows)} rows; m08a_corrections.csv {len(rows)} rows")


if __name__ == "__main__":
    main()
