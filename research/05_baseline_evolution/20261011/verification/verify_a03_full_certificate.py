"""Verify the saved sparse certificate with Python's exact Fraction arithmetic.

Usage: python verify_a03_full_certificate.py [path/to/evidence/a03_full_lp]
Reads only saved JSON row fragments; no source matrix scan or solver is used.
Its conclusion is conditional on the separately recorded source identity and
complete-support extraction receipt; those bind fragments to the frozen LP.
"""
import collections
import hashlib
import json
import math
import sys
from fractions import Fraction as Q
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rational(hex_value):
    value = float.fromhex(hex_value)
    if not math.isfinite(value):
        raise ValueError("A finite certificate coefficient/RHS is required")
    return Q(value)


def verify(root):
    receipt = load(root / "COMPLETE_SUPPORT_RECEIPT.json")
    selection = load(root / "TARGET_ROW_SELECTION.json")
    identity = load(root / "FROZEN_IDENTITY_CHECK.json")
    assert receipt["one_CSC_structure_pass"] and receipt["entries_scanned"] == 90782037
    assert identity["all_source_stat_unchanged"]
    assert len(identity["array_identities"]) == 12
    assert all(x["sha256"] == x["expected_sha256"] for x in identity["array_identities"])
    expected_rows = {r for f in selection["families"] for r in f["rows"]}
    assert len(expected_rows) == selection["target_row_count"] == 26284
    assert len(expected_rows) == sum(len(f["rows"]) for f in selection["families"])
    scale_meta = receipt["scales_file"]
    assert digest(root / scale_meta["file"]) == scale_meta["sha256"]
    scales = {}
    for group in load(root / scale_meta["file"])["groups"]:
        d = rational(group["D_hex"])
        assert d > 0
        for col in group["columns"]:
            assert col not in scales
            scales[col] = d

    eq_lhs = collections.defaultdict(Q)
    lower_lhs = collections.defaultdict(Q)
    rhs_eq = Q(0)
    rhs_lower = Q(0)
    demand = Q(0)
    stock = Q(0)
    seen = set()
    multipliers = []
    terms_count = 0
    for shard in receipt["shards"]:
        path = root / shard["file"]
        assert path.parent == root and path.stat().st_size == shard["bytes"]
        assert digest(path) == shard["sha256"]
        data = load(path)
        meta = data["metadata"]
        family = meta["family"]
        lower = family == "Store-fix-e-lower"
        # Multipliers are derived here independently of scanner formula checks.
        lam = Q(1 if lower or family == "Store-energy_balance" else 3)
        mus = set()
        used_rows = []
        assert meta["complete_row_support"]
        assert len(data["rows"]) == shard["row_count"] == meta["row_count"]
        for row, lo_hex, hi_hex, r_hex, terms in data["rows"]:
            assert row in expected_rows and row not in seen
            seen.add(row)
            used_rows.append(row)
            r = rational(r_hex)
            assert r > 0
            mu = lam / r
            mus.add(str(mu))
            rhs = rational(lo_hex)
            if lower:
                assert float.fromhex(hi_hex) == math.inf and rhs == 0 and mu >= 0
                rhs_lower += mu * rhs
            else:
                assert rhs == rational(hi_hex)
                rhs_eq += mu * rhs
                if family == "Store-energy_balance":
                    stock -= rhs / r
                elif meta["asset"] == selection["group"]:
                    demand += Q(3) * rhs / r
            assert len(terms) == len({col for col, _ in terms})
            terms_count += len(terms)
            accumulator = lower_lhs if lower else eq_lhs
            for col, value_hex in terms:
                assert col in scales
                accumulator[col] += mu * rational(value_hex)
        multipliers.append({"support_file": shard["file"], "relation": ">=" if lower else "=",
                            "source_bound": "lower" if lower else "equal_lower_and_upper",
                            "rows": used_rows, "original_unit_multiplier": str(lam),
                            "native_multiplier_values": sorted(mus),
                            "native_multiplier_rule": "original_unit_multiplier / R[row]"})
    assert seen == expected_rows and terms_count == receipt["target_entries"]
    eq_nonzero = {col: v for col, v in eq_lhs.items() if v}
    combined = {col: eq_lhs[col] + lower_lhs[col] for col in set(eq_lhs) | set(lower_lhs)}
    nonzero = {col: str(v) for col, v in combined.items() if v}
    rhs = rhs_eq + rhs_lower
    gap_ok = demand - stock == rhs_eq == Q(513, 34359738368)
    proved = not nonzero and rhs > 0 and gap_ok
    return {"status": "FULL_LP_EXACT_INFEASIBILITY_CERTIFIED" if proved else "CERTIFICATE_NOT_ESTABLISHED",
            "certificate_convention": "Equalities may have signed multipliers; lower inequalities have nonnegative multipliers. Sum yields 0 >= strictly positive RHS.",
            "exact_arithmetic": "Fraction(float.fromhex(...)); exact binary64 rational values; no tolerance or approximate comparison",
            "source_complete_support_receipt_sha256": digest(root / "COMPLETE_SUPPORT_RECEIPT.json"),
            "source_identity_check_sha256": digest(root / "FROZEN_IDENTITY_CHECK.json"),
            "target_row_selection_sha256": digest(root / "TARGET_ROW_SELECTION.json"),
            "verified_rows": len(seen), "verified_stored_terms": terms_count,
            "equality_rows": sum(len(x["rows"]) for x in multipliers if x["relation"] == "="),
            "lower_bound_rows": sum(len(x["rows"]) for x in multipliers if x["relation"] == ">="),
            "row_multipliers": multipliers,
            "equality_remaining_native_coefficients": {str(k): str(v) for k, v in sorted(eq_nonzero.items())},
            "equality_remaining_original_unit_coefficients": {str(k): str(v / scales[k]) for k, v in sorted(eq_nonzero.items())},
            "lower_combination_native_coefficients": {str(k): str(v) for k, v in sorted(lower_lhs.items()) if v},
            "combined_nonzero_coefficients": nonzero,
            "exact_annual_demand_mwh": str(demand), "exact_initial_stock_mwh": str(stock),
            "exact_gap_mwh": str(demand - stock), "combined_exact_rhs_mwh": str(rhs),
            "contradiction": "0 >= 513/34359738368 MWh > 0" if proved else None,
            "full_lp_scope": "Frozen finite binary64 coefficients interpreted as exact real/rational constraints, independent of objective; not a claim about tolerance acceptance or scientific repair.",
            "solver_calls": 0, "source_matrix_scans": 0}


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (Path(__file__).resolve().parents[1] / "evidence/a03_full_lp")
    result = verify(root)
    print(json.dumps({k: v for k, v in result.items() if k != "row_multipliers"}, ensure_ascii=False, indent=2))
