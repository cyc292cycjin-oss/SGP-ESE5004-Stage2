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


def input_fx():
    return float(pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id").loc["fx_usd_to_eur_2020", "value"])


def test_usd_columns_equal_eur_times_rate():
    from phase4_static import config
    cfg = config(ROOT, "integrated")
    rep = report_currency(cfg)
    fx = 1.0 / input_fx()                                                                # supplement 01 item 3: inverse of the input row
    assert rep["currency"] == "USD2020" and rep["fx_per_eur2020"] == fx and rep["rule"] == "inverse_of_input" and rep["consistent_with_input"] is True
    assert rep["fx_per_eur2020"] == pytest.approx(1.139954, abs=5e-7) and rep["ecb_2020_reference"] == 1.1422
    L = toy_ledger(); D = ledger_detail_usd(L, rep["fx_per_eur2020"])
    assert (D.usd2020 == D.eur * fx).all() and (D.usd2020_length_split == D.eur_length_split * fx).all()
    assert list(D.columns[:5]) == list(L.columns) and (D.eur == L.eur).all()          # EUR2020 columns unchanged
    T = ledger_table(L); U = ledger_table_usd(T, rep["fx_per_eur2020"])
    assert list(U.columns) == list(T.columns) and U.at["VN", "total"] == pytest.approx(1.5e9 * fx) and U.at["SG", "total_length_split"] == pytest.approx(1.9e8 * fx)
    bad = copy.deepcopy(cfg); bad["research"]["reporting"]["currency"] = "USD2024"
    with pytest.raises(ValueError):
        report_currency(bad)
    bad = copy.deepcopy(cfg); bad["research"]["reporting"]["fx_per_eur2020"] = "ecb"
    with pytest.raises(ValueError):
        report_currency(bad)
    ecb = copy.deepcopy(cfg); ecb["research"]["reporting"]["fx_per_eur2020"] = 1.1422   # comparison value: accepted, flagged
    r = report_currency(ecb)
    assert r["fx_per_eur2020"] == 1.1422 and r["consistent_with_input"] is False


def test_round_trip_usd_input():
    """One rate both ways: a USD input converted to EUR2020 with fx_usd_to_eur_2020 and reported back in USD2020 returns its own value."""
    from phase4_static import config
    rep = report_currency(config(ROOT, "integrated"))
    usd = pd.Series([9.7, 76.0, 84.0, 1.0e9])                                          # e.g. WEO gas / oil / coal prices, a USD capex
    back = ledger_detail_usd(pd.DataFrame(dict(eur=usd * input_fx(), eur_length_split=usd * input_fx())), rep["fx_per_eur2020"]).usd2020
    assert (abs(back / usd - 1.0) < 1e-14).all()


def test_reporting_not_in_g22_subset():
    sys.path.insert(0, str(ROOT / "scripts_project" / "v5"))
    from gates_v6 import config_subset_sha256
    from phase4_static import config
    R = config(ROOT, "integrated")["research"]; r = copy.deepcopy(R); r["reporting"]["fx_per_eur2020"] = 1.0
    assert config_subset_sha256(R) == config_subset_sha256(r)


def test_registry_rows():
    r = pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")
    fx = float(r.loc["fx_usd_to_eur_2020", "value"])
    assert float(r.loc["report_currency_rule", "value"]) == pytest.approx(1.0 / fx, rel=1e-11) and r.loc["report_currency_rule", "unit"] == "USD2020/EUR2020"
    assert r.loc["report_currency_rule", "source"] == r.loc["fx_usd_to_eur_2020", "source"] and r.loc["report_currency_rule", "status"] == "REGISTERED"
    assert float(r.loc["fx_report_ecb_2020_reference", "value"]) == 1.1422 and r.loc["fx_report_ecb_2020_reference", "status"] == "REFERENCE_ONLY"
    assert "fx_report_vs_input_rate_note" not in r.index
