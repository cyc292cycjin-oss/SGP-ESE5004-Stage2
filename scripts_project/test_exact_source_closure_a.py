"""Focused non-solver regression checks for the approved derivation and whitelist."""
import copy, importlib.util, json, math, struct, sys, unittest
from pathlib import Path
from fractions import Fraction as F

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'scripts_project'))
import exact_source_closure_a as builder
import verify_exact_source_closure_a as verifier

class ControlledClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(sys.argv[1]) if len(sys.argv)>1 and not sys.argv[1].startswith('-') else Path('/mnt/d/ResearchWorkspaces/ASEAN/outputs/phase4_gate4_final_closure_20261006')
        cls.old=verifier.read(root/'production_assets/carrier_fragment.json')
        cls.old_a=verifier.read(root/'production_assets/external_pending_fixed_accounts.json')
        out=REPO/builder.DERIVED
        cls.new=verifier.read(out/'carrier_fragment.json');cls.new_a=verifier.read(out/'external_pending_fixed_accounts.json')
        cls.changes=verifier.approved_changes(verifier.read(REPO/builder.AUDIT/builder.APPROVED['option_a'][0]))
        cls.first=next(iter(cls.changes))

    def check_rejected(self,n=None,a=None):
        with self.assertRaises(ValueError):
            verifier.validate_diff(self.old,self.new if n is None else n,self.old_a,self.new_a if a is None else a,self.changes)

    def test_01_real_whitelist_pass(self):
        self.assertEqual(len(verifier.validate_diff(self.old,self.new,self.old_a,self.new_a,self.changes)),720)

    def test_02_unsynced_e_initial_rejected(self):
        n=copy.deepcopy(self.new);n['components']['Store:'+self.first]['params']['e_initial']=self.old['components']['Store:'+self.first]['params']['e_initial'];self.check_rejected(n)

    def test_03_unsynced_route_rejected(self):
        n=copy.deepcopy(self.new);n['biomass_obligation_routes'][self.first]['annual_cap_mwh']=self.old['biomass_obligation_routes'][self.first]['annual_cap_mwh'];self.check_rejected(n)

    def test_04_unsynced_external_rejected(self):
        a=copy.deepcopy(self.new_a);i=next(i for i,x in enumerate(a) if x['FixedAccountID']==self.first);a[i]['QuantityMWh']=self.old_a[i]['QuantityMWh'];self.check_rejected(a=a)

    def test_05_one_extra_ulp_rejected(self):
        n=copy.deepcopy(self.new);p=n['components']['Store:'+self.first]['params'];p['e_nom']=math.nextafter(p['e_nom'],math.inf);self.check_rejected(n)

    def test_06_animal_change_rejected(self):
        a=copy.deepcopy(self.new_a);x=next(x for x in a if x['Commodity']=='Animal waste');x['QuantityMWh']=math.nextafter(x['QuantityMWh'],math.inf);self.check_rejected(a=a)

    def test_07_new_Load_rejected(self):
        n=copy.deepcopy(self.new);n['components']['Load:unexpected']={'type':'Load'};self.check_rejected(n)

    def test_08_port_change_rejected(self):
        n=copy.deepcopy(self.new);meter=next(x['Meter'] for x in self.new_a if x['FixedAccountID']==self.first);n['components']['Link:'+meter]['outputs']=['other Bus'];self.check_rejected(n)

    def test_09_NULL_price_change_rejected(self):
        a=copy.deepcopy(self.new_a);a[0]['UnitPriceEUR2020PerMWh']=0.;self.check_rejected(a=a)

    def test_10_negative_zero_detected(self):
        self.assertEqual(len(verifier.differences(0.,-0.)),1)

    def test_11_ceil_exact_and_upward(self):
        for x in [F(1),F(1)+F(1,2**54),F(66215441.239243574)+F(513,34359738368)]:
            y=builder.ceil_binary64(x);self.assertLess(F(math.nextafter(y,-math.inf)),x);self.assertGreaterEqual(F(y),x)

    def test_12_existing_version_refuses_overwrite(self):
        with self.assertRaisesRegex(ValueError,'output exists'):
            builder.derive(REPO,Path('/not/read'),REPO/builder.DERIVED)

    def test_13_asset_removal_rejected(self):
        n=copy.deepcopy(self.new);del n['components']['Store:'+self.first];self.check_rejected(n)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ControlledClosureTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    evidence=REPO/builder.AUDIT/'implementation_a_v1'
    evidence.mkdir(exist_ok=True)
    with (evidence/'FOCUSED_TEST_RECEIPT.json').open('x',encoding='utf-8') as f:
        json.dump({'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'status':'PASS' if result.wasSuccessful() else 'FAIL','scope':'new derivation only; in-memory mutations, no source writes or solver',
            'test_file_sha256':verifier.digest(Path(__file__)),'generator_sha256':verifier.digest(REPO/'scripts_project/exact_source_closure_a.py'),
            'verifier_sha256':verifier.digest(REPO/'scripts_project/verify_exact_source_closure_a.py')},f,indent=2);f.write('\n')
    sys.exit(not result.wasSuccessful())
