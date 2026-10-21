"""M08a A9 / M08-10 (decisions 125 (4), 133): ledger exports with USD2020 columns, model in EUR2020 (no build, no solve)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4d_ledger import ledger_detail_usd, ledger_table, ledger_table_usd, report_currency   # noqa: E402

REG = ROOT / "research_inputs" / "registry_v5" / "DATA_REGISTRY.csv"


def toy_ledger():
    return pd.DataFrame([dict(entity="VN", subject="investment", carrier="solar", eur=1e9, eur_length_split=1.1e9),
                         dict(entity="VN", subject="variable", carrier="gas", eur=5e8, eur_length_split=5e8),
                         dict(entity="SG", subject="investment", carrier="solar", eur=2e8, eur_length_split=1.9e8)])


def test_usd_columns_equal_eur_times_rate():
    from phase4_static import config
    cfg = config(ROOT, "integrated")
    rep = report_currency(cfg)
    assert rep == dict(currency="USD2020", fx_per_eur2020=1.1422)
    L = toy_ledger(); D = ledger_detail_usd(L, rep["fx_per_eur2020"])
    assert (D.usd2020 == D.eur * 1.1422).all() and (D.usd2020_length_split == D.eur_length_split * 1.1422).all()
    assert list(D.columns[:5]) == list(L.columns) and (D.eur == L.eur).all()          # EUR2020 columns unchanged
    T = ledger_table(L); U = ledger_table_usd(T, rep["fx_per_eur2020"])
    assert list(U.columns) == list(T.columns) and U.at["VN", "total"] == pytest.approx(1.5e9 * 1.1422) and U.at["SG", "total_length_split"] == pytest.approx(1.9e8 * 1.1422)
    bad = copy.deepcopy(cfg); bad["research"]["reporting"]["currency"] = "USD2024"
    with pytest.raises(ValueError):
        report_currency(bad)


def test_reporting_not_in_g22_subset():
    sys.path.insert(0, str(ROOT / "scripts_project" / "v5"))
    from gates_v6 import config_subset_sha256
    from phase4_static import config
    R = config(ROOT, "integrated")["research"]; r = copy.deepcopy(R); r["reporting"]["fx_per_eur2020"] = 1.0
    assert config_subset_sha256(R) == config_subset_sha256(r)


def test_registry_rows():
    r = pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")
    assert float(r.loc["report_currency_rule", "value"]) == 1.1422 and r.loc["report_currency_rule", "unit"] == "USD2020/EUR2020"
    fx = float(r.loc["fx_usd_to_eur_2020", "value"])
    assert float(r.loc["fx_report_vs_input_rate_note", "value"]) == pytest.approx(1.1422 * fx - 1, rel=1e-9) and abs(1.1422 * fx - 1) < 0.003
