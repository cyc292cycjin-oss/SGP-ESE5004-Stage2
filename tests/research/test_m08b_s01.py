"""M08b supplement 01 (decision 137): review decisions D (GATES_V6 SHA choice), 8, 9, 11 and the registered limitations (no build, no solve)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
sys.path.insert(0, str(ROOT / "scripts_project" / "v5"))
import gates_v6 as g6   # noqa: E402

BR = dict(network=dict(sha256="a" * 64, snapshots=2920), daily_network=dict(sha256="d" * 64, snapshots=365))


def rec(snapshots, truncated_to=None):
    return dict(input_network=dict(sha256="x" * 64, snapshots=snapshots, truncated_to=truncated_to))


def test_registered_sha_truncated_runs_take_the_2920_network():
    """item D: only an untruncated 365-snapshot run is checked against the 365x24h network; a truncated run of the 2920x3h file (56 snapshots,
    or a 365-snapshot probe) and a full 2920x3h run against the 2920x3h network of the build receipt."""
    assert g6.registered_sha_from_build_receipt(BR, rec(56, 56)) == "a" * 64            # M08b smoke: --truncate 56 on the 2920x3h file
    assert g6.registered_sha_from_build_receipt(BR, rec(365, 365)) == "a" * 64          # a 365-snapshot probe of the 2920x3h file
    assert g6.registered_sha_from_build_receipt(BR, rec(2920)) == "a" * 64
    assert g6.registered_sha_from_build_receipt(BR, rec(365)) == "d" * 64               # untruncated 365x24h run (level 2)
    assert g6.registered_sha_from_build_receipt(BR, rec(365, 0)) == "d" * 64            # --truncate 0 = no truncation
    assert g6.registered_sha_from_build_receipt(dict(network=BR["network"]), rec(365)) == "a" * 64   # receipt without a daily network
    assert g6.registered_sha_from_build_receipt(BR, None) == "a" * 64
