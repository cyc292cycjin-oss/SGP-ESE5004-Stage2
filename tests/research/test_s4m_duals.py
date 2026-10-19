"""S4M supplement 01: the per-constraint dual export must handle constraints that share a dim name with conflicting coordinates (m.dual fails there)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))


def test_dual_dataset_with_conflicting_dim_coords(tmp_path):
    import linopy
    from s4m_duals import write_duals
    m = linopy.Model()
    sn = pd.Index([0, 1], name="snapshot")
    g_fix = m.add_variables(lower=0, coords=[sn, pd.Index(["g1", "g2"], name="Generator")], name="Generator-fix-p")
    g_ext = m.add_variables(lower=0, coords=[sn, pd.Index(["g3"], name="Generator")], name="Generator-ext-p")   # same dim name 'Generator', different coords
    m.add_constraints(g_fix <= 5, name="Generator-fix-p-upper"); m.add_constraints(g_ext <= 1, name="Generator-ext-p-upper")
    m.add_constraints(g_fix.sum("Generator") + g_ext.sum("Generator") >= 4, name="Bus-nodal_balance")
    m.add_constraints(g_ext.sum() >= 0.5, name="ResearchImportAnnual-TH2 1 gas production")
    m.add_objective(2 * g_fix.sum() + g_ext.sum())
    m.solve(solver_name="highs")
    res = write_duals(m, tmp_path)   # m.dual raised 'conflicting values for variable Generator' on the research model; the per-constraint export must not depend on it
    assert res["constraints"] == 4 and res["research_constraints"] == 1 and not res["unassigned"]
    D = xr.open_dataset(tmp_path / "DUALS_BY_CONSTRAINT.nc")
    assert set(D.data_vars) == {"Generator-fix-p-upper", "Generator-ext-p-upper", "Bus-nodal_balance", "ResearchImportAnnual-TH2 1 gas production"}
    assert D["Generator-ext-p-upper"].dims == ("Generator-ext-p-upper|snapshot", "Generator-ext-p-upper|Generator")
    nb = D["Bus-nodal_balance"].values; assert np.all(np.isfinite(nb)) and nb.shape == (2,)
    idx = pd.read_csv(tmp_path / "DUALS_INDEX.csv"); assert int(idx["size"].sum()) == 4 + 2 + 2 + 1
