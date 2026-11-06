"""V4 D1 (decisions 212, 214, 215; V4_D1_INSTRUCTION.md sections 3-5): registry rows of the D1 data step, assembled into DATA_REGISTRY.csv by
scripts_project/d1_registry.py.

    PYTHONHASHSEED=0 python scripts_project/v4_d1_registry.py && python scripts_project/d1_registry.py

  fragments/v4_d1.csv   new rows: the missing-cost rule of the biomass pools (section 3; value read from the registry proxy rows of unsourced residues).
Deterministic (no time stamps). Nothing is solved.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from d1_common import REG_DIR, Registry   # noqa: E402
from s2_layers import MISSING_COST_PROXY_ID, MISSING_COST_PROXY_SOURCE   # noqa: E402

SCRIPT = "scripts_project/v4_d1_registry.py"


def proxy_rows(reg: pd.DataFrame) -> pd.DataFrame:
    """Registry biomass cost rows priced with the uniform proxy of unsourced residues (cassava / coconut / other crop residues)."""
    return reg[reg.param_id.str.startswith("biomass_cost_") & reg.source.str.startswith(MISSING_COST_PROXY_SOURCE)]


def missing_cost_row(r: Registry, reg: pd.DataFrame) -> None:
    peers = proxy_rows(reg)
    vals = sorted(set(peers.value.astype(float)))
    if len(vals) != 1:
        raise SystemExit(f"the registry proxy rows of unsourced residues carry {len(vals)} values: {vals}")
    lo = sorted(set(peers.sensitivity_low.astype(float))); hi = sorted(set(peers.sensitivity_high.astype(float)))
    p0 = peers.iloc[0]
    pend = reg[reg.param_id.str.startswith("biomass_cost_") & (reg.status == "DATA_PENDING")].param_id.tolist()
    r.add(MISSING_COST_PROXY_ID,
          "uniform feedstock cost of biomass pools whose registry cost is DATA_PENDING and whose cost column is empty (research.biomass.missing_cost_rule = "
          f"proxy; v4 main; v3.1 = zero, i.e. 0 EUR/MWh): the registry proxy of unsourced residues ({len(peers)} rows biomass_cost_*_cassava / coconut / "
          f"other_crop_residues: {MISSING_COST_PROXY_SOURCE}); applies to {', '.join(pend)}. Grade for oil palm trunk: D (generic residue proxy, no trunk "
          "felling / chipping / transport cost; candidates in DOWNLOAD_CANDIDATES.csv of V4 D1)",
          vals[0], "EUR2020/MWh", "C", f"{MISSING_COST_PROXY_SOURCE} (registry proxy of unsourced residues; decisions 212 item 5, 215 item 5)",
          f"research_inputs/registry_v5/DATA_REGISTRY.csv: biomass_cost_* rows whose source starts with '{MISSING_COST_PROXY_SOURCE}' ({len(peers)} rows; {p0.source_locator})",
          p0.source_sha256, sensitivity_low=lo[0] if len(lo) == 1 else None, sensitivity_high=hi[0] if len(hi) == 1 else None,
          decision_ref="212 item 5, 215 item 5", status="REGISTERED")


def main():
    reg = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False)
    r = Registry(SCRIPT)
    missing_cost_row(r, reg)
    out = REG_DIR / "fragments" / "v4_d1.csv"
    r.write(out)
    print(out, len(r.rows))


if __name__ == "__main__":
    main()
