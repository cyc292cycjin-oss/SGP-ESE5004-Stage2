"""S4H-3 registry fragment s4h_3: the decision-100 IPP export-line estimate against the LA / VN ledger differences of the S4H-3 smoke
(instruction S4H-1: 'compare with the LA and VN country-ledger differences, write into the report and the registry').

    python scripts_project/s4h_3_registry.py
"""
from __future__ import annotations

import json

from d1_common import REG_DIR, ROOT, Registry, sha256

SCRIPT = "scripts_project/s4h_3_registry.py"
SUMMARY = ROOT / "results_project/s4h/s4h3/analysis/S4H3_SMOKE_SUMMARY.json"
EVIDENCE = "research/06_scope_redesign/p1_step4h_20261017/evidence/s4h_3/S4H3_SMOKE_SUMMARY.json"


def main():
    s = json.loads(SUMMARY.read_text()); ipp = s["ipp_vs_ledger"]; f = s["focus"]
    lo, hi = ipp["ipp_bn_eur_per_a"]; la, vn = f["LA"]["disconnected_minus_integrated"], f["VN"]["disconnected_minus_integrated"]
    reg = Registry(SCRIPT)
    reg.add("s4h3_ipp_vs_ledger_smoke", f"Decision 100 limitation vs the S4H-3 smoke ledgers (56 snapshots, SMOKE_TEST_ONLY; scale not judged, decision 47): IPP export-line "
            f"estimate {lo * 1e3:.1f}-{hi * 1e3:.1f} M EUR/a against disconnected - integrated LA {la:.2f} bn EUR and VN {vn:.2f} bn EUR "
            f"({lo / la * 100:.2f}-{hi / la * 100:.2f} % of LA, {lo / vn * 100:.3f}-{hi / vn * 100:.3f} % of VN); integrated ledger vs S4G-3: LA "
            f"{ipp['ledger_integrated_change_vs_s4g_bn_eur']['LA']:+.2f}, VN {ipp['ledger_integrated_change_vs_s4g_bn_eur']['VN']:+.2f} bn EUR (all S4H changes together)",
            hi * 1e9, "EUR/a", "C", "derived (scripts_project/s4h_3_registry.py from the S4H-3 smoke summary)", EVIDENCE, sha256(SUMMARY),
            sensitivity_low=lo * 1e9, sensitivity_high=hi * 1e9, decision_ref="100", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4h_3.csv")
    print("registry fragment s4h_3 written")


if __name__ == "__main__":
    main()
