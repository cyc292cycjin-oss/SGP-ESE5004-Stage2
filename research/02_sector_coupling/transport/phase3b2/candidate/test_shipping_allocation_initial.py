"""Offline regression of the real add_shipping constructor; never runs a solver.

Small numbers are TEST FIXTURES, not ASEAN demand/share assumptions. GIS mapping
is stubbed explicitly, so this tests accounting and indexing, not geolocation.
"""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
import numpy as np
import pandas as pd

ROOT = Path(sys.argv.pop(1)).resolve()
OUT = Path(sys.argv.pop(1)).resolve()


def constructor():
    tree = ast.parse((ROOT / "scripts/prepare_sector_network.py").read_text())
    fun = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "add_shipping")
    namespace = {"pd": pd, "pypsa": types.SimpleNamespace(Network=object)}
    helper = ROOT / "scripts/_shipping_allocation.py"
    if helper.exists():
        spec = importlib.util.spec_from_file_location("shipping_candidate", helper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        namespace["allocate_shipping_demand"] = module.allocate_shipping_demand
    exec(compile(ast.Module(body=[fun], type_ignores=[]), str(ROOT), "exec"), namespace)
    return namespace


class CaptureNetwork:
    def __init__(self, countries=None):
        self.buses = pd.DataFrame({"carrier": ["AC", "AC", "AC"], "country": ["ID", "ID", "SG"]}, index=pd.Index(["ID0", "ID1", "SG0"], name="Bus"))
        if countries:
            for country in countries:
                self.buses.loc[country + "0"] = ["AC", country]
        self.stores = pd.DataFrame({"carrier": ["oil"]})
        self.generators = pd.DataFrame({"carrier": ["oil"]})
        self.records = {}
    def madd(self, component, names, **kw):
        if component == "Load":
            val = kw["p_set"].reindex(names)
            self.records[kw["carrier"]] = val
    def add(self, component, name, **kw):
        pass


def fixture():
    national = pd.DataFrame({"total international navigation": [7., 11.], "total domestic navigation": [1., 1.]}, index=["ID", "SG"])
    ports = pd.DataFrame({"country": ["ID", "ID", "SG"], "fraction": [.4, .6, 1.], "gadm_1": ["ID0", "ID0", "SG0"]})
    return national, ports


def run(national, ports):
    ns = constructor()
    extras = set(national.index) - {"ID", "SG"}
    n = CaptureNetwork(extras)
    nodes = n.buses.index
    ns.update(countries=list(national.index), demand_sc="TEST_FIXTURE", investment_year=2030,
              options={"shipping_average_efficiency": .4, "shipping_hydrogen_share": 0., "shipping_hydrogen_liquefaction": False},
              get=lambda x, _: x, read_csv_nafix=lambda *a, **kw: ports.copy(),
              locate_bus=lambda p, *args: p.copy(),
              snakemake=types.SimpleNamespace(params=types.SimpleNamespace(gadm_layer_id=1, alternative_clustering=False, h2_policy={"is_reference": False, "remove_h2_load": False}, sector_options={"international_bunkers": True}), input=types.SimpleNamespace(shapes_path="STUB_NOT_USED")),
              spatial=types.SimpleNamespace(nodes=nodes, oil=types.SimpleNamespace(nodes=nodes + " oil", locations=nodes)))
    costs = pd.DataFrame({"efficiency": {"fuel cell": .5}, "CO2 intensity": {"oil": 1.}})
    ns["add_shipping"](n, costs, national, "STUB_NOT_USED")
    return n


class ShippingRegression(unittest.TestCase):
    def setUp(self): self.national, self.ports = fixture()
    def reject(self, text):
        with self.assertRaisesRegex(ValueError, "shipping allocation:.*" + text):
            run(self.national, self.ports)
    def test_repeated_ports_same_node_country_totals(self):
        n = run(self.national, self.ports)
        oil = n.records["shipping oil"] * 8760 / 1e6
        self.assertTrue(np.isfinite(oil).all(), oil.to_dict())
        np.testing.assert_allclose(oil.groupby(n.buses.country).sum().loc[self.national.index], [8., 12.])
    def test_node_without_port_is_structural_zero(self):
        n = run(self.national, self.ports)
        self.assertEqual(n.records["shipping oil"].loc["ID1"], 0.)
        self.assertTrue(np.isfinite(n.records["H2 for shipping"]).all())
    def test_domestic_and_bunker_each_conserved(self):
        ns = constructor()
        self.assertIn("allocate_shipping_demand", ns)
        p = self.ports.set_index("gadm_1")
        out = ns["allocate_shipping_demand"](p, self.national, CaptureNetwork().buses)
        np.testing.assert_allclose(out.groupby(CaptureNetwork().buses.country).sum().loc[self.national.index], self.national)
    def test_source_tables_not_mutated(self):
        before = self.national.copy(deep=True)
        p = self.ports.copy(deep=True)
        run(self.national, self.ports)
        pd.testing.assert_frame_equal(self.national, before)
        pd.testing.assert_frame_equal(self.ports, p)
    def test_one_missing_account_is_not_summed_as_zero(self):
        self.national.iloc[0, 0] = np.nan
        self.reject("national account")
    def test_infinite_national_account_rejected(self):
        self.national.iloc[0, 0] = np.inf
        self.reject("national account")
    def test_negative_national_account_rejected(self):
        self.national.iloc[0, 0] = -1
        self.reject("national account")
    def test_missing_weight_rejected(self):
        self.ports.loc[0, "fraction"] = np.nan
        self.reject("fraction")
    def test_negative_weight_rejected(self):
        self.ports.loc[0, "fraction"] = -.1
        self.reject("fraction")
    def test_weights_not_normalized_rejected(self):
        self.ports.loc[0, "fraction"] = .3
        self.reject("sum to one")
    def test_nonzero_country_without_port_rejected(self):
        self.national.loc["BN"] = [1., 2.]
        self.reject("no ports")
    def test_explicit_source_zero_country_without_port(self):
        self.national.loc["BN"] = [0., 0.]
        n = run(self.national, self.ports)
        self.assertEqual(n.records["shipping oil"].loc["BN0"], 0.)
    def test_unknown_node_rejected(self):
        self.ports.loc[0, "gadm_1"] = "UNKNOWN"
        self.reject("unknown AC node")
    def test_cross_country_node_rejected(self):
        self.ports.loc[0, "gadm_1"] = "SG0"
        self.reject("country boundary")
    def test_duplicate_national_country_rejected(self):
        self.national = pd.concat([self.national, self.national.loc[["ID"]]])
        self.reject("duplicate country")


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *a, **kw): super().__init__(*a, **kw); self.rows = []
    def addSuccess(self, t): super().addSuccess(t); self.rows.append({"test": t._testMethodName, "status": "PASS"})
    def addFailure(self, t, e): super().addFailure(t, e); self.rows.append({"test": t._testMethodName, "status": "FAIL", "detail": self._exc_info_to_string(e,t)})
    def addError(self, t, e): super().addError(t, e); self.rows.append({"test": t._testMethodName, "status": "ERROR", "detail": self._exc_info_to_string(e,t)})

if __name__ == "__main__":
    r = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(ShippingRegression))
    OUT.write_text(json.dumps({"source": str(ROOT), "scope": "OFFLINE_CONSTRUCTOR_WITH_STUBBED_GIS_NO_SOLVE", "fixture_not_model_data": True, "python": sys.version, "pandas": pd.__version__, "numpy": np.__version__, "tests": r.rows, "passed": r.wasSuccessful()}, indent=2))
    sys.exit(0 if r.wasSuccessful() else 1)
