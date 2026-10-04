"""Adversarial synthetic tests for reusable static hooks, no solver calls."""
import unittest, sys, tempfile, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import pypsa
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts_project'))
import phase4_static as v

class Validation(unittest.TestCase):
    def setUp(self):
        self.a=pd.DataFrame({'electricity':[3.,5.]},index=['SG','MY'])
    def test_valid_demand(self): self.assertTrue(v.demand(self.a))
    def test_nan_inf(self):
        for x in [np.nan,np.inf,-np.inf]:
            a=self.a.copy();a.iloc[0,0]=x
            with self.assertRaises(ValueError):v.demand(a)
    def test_negative(self):
        with self.assertRaises(ValueError):v.demand(-self.a)
    def test_duplicate(self):
        with self.assertRaises(ValueError):v.demand(pd.concat([self.a,self.a]))
    def test_empty(self):
        with self.assertRaises(ValueError):v.demand(self.a.iloc[:0])
    def test_conservation_order(self): self.assertTrue(v.conserve(self.a,self.a.iloc[::-1]))
    def test_equal_total_wrong_country(self):
        with self.assertRaises(ValueError):v.conserve(self.a,self.a.assign(electricity=[5.,3.]))
    def test_missing_country(self):
        with self.assertRaises(ValueError):v.conserve(self.a,self.a.iloc[:1])
    def test_allocation(self):
        a=pd.DataFrame({'electricity':[1.,2.,5.]},index=['S0','S1','M0'])
        self.assertTrue(v.allocation(self.a,a,pd.Series(['SG','SG','MY'],index=a.index)))
        with self.assertRaises(ValueError):v.allocation(self.a,a,pd.Series(['SG'],index=['S0']))
    def net(self):
        n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=2,freq='3h'))
        n.snapshot_weightings.loc[:,:]=3.
        n.add('Bus','SG0',carrier='AC');n.add('Bus','MY0',carrier='AC')
        # country is project metadata, not a PyPSA 0.30.3 built-in attribute.
        n.buses['country']=pd.Series({'SG0':'SG','MY0':'MY'})
        n.add('Bus','Earth oil',carrier='oil');n.add('Load','fixed',bus='SG0',p_set=2)
        n.add('Load','varying',bus='MY0',p_set=[1.,3.])
        n.add('Link','border',bus0='SG0',bus1='MY0',carrier='DC',p_nom=1.)
        n.add('Link','oil conversion',bus0='Earth oil',bus1='SG0',carrier='oil',p_nom_extendable=True)
        return n
    def test_weighted_load(self): self.assertEqual(v.annual_loads(self.net()).to_dict(),{'fixed':12.,'varying':12.})
    def test_weights(self):
        n=self.net();v.snapshot_weights(n,{'generators':6.})
        with self.assertRaises(ValueError):v.snapshot_weights(n,{'generators':8760.})
        n.snapshot_weightings.iloc[0,0]=0
        with self.assertRaises(ValueError):v.snapshot_weights(n)
    def test_dynamic_nan(self):
        n=self.net();n.loads_t.p_set.iloc[0,0]=np.nan
        with self.assertRaises(ValueError):v.annual_loads(n)
    def test_border_shared_coupling(self):
        r=v.inventory(self.net());self.assertEqual(r['edges'][0]['classification'],'CROSS_BORDER')
        self.assertEqual(r['edges'][1]['classification'],'SHARED_POOL')
        self.assertEqual(len(r['coupling']),1)
    def test_unknown_is_not_domestic(self):
        n=self.net();n.buses.loc['MY0','country']=''
        self.assertEqual(v.inventory(n)['edges'][0]['classification'],'UNKNOWN')
    def test_earth_location_does_not_prove_shared_pool(self):
        self.assertEqual(v.bus_scope('SG0 biogas',pd.Series({'location':'Earth'}))[0],'UNKNOWN')
    def test_missing_endpoint(self):
        n=self.net();n.links.loc['border','bus1']='missing'
        self.assertEqual(v.inventory(n)['edges'][0]['classification'],'INVALID_ENDPOINT')
    def test_pending_not_pass(self):
        r=v.preflight(self.net());self.assertEqual(r['E']['status'],'PENDING')
        self.assertEqual(r['K']['status'],'PENDING');self.assertFalse(r['full_sc_assembled'])
    def test_carbon_detection_not_scope_approval(self):
        n=self.net();n.add('GlobalConstraint','CO2Limit',type='primary_energy',carrier_attribute='co2_emissions',constant=123.)
        r=v.preflight(n)
        self.assertEqual(r['inventory']['policy_constraints'][0]['constant'],123.)
        self.assertEqual(r['K']['status'],'PENDING')
    def test_identity(self):
        repo=Path(__file__).resolve().parents[2]
        h=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
        v.identity(repo,h,{'config.default.yaml':v.sha256(repo/'config.default.yaml')})
        with self.assertRaises(ValueError):v.identity(repo,'0'*40,{})
        with self.assertRaises(ValueError):v.identity(repo,h,{'config.default.yaml':'0'*64})
    def test_config_no_scenario_difference(self):
        repo=Path(__file__).resolve().parents[2]
        baseline=v.config(repo)
        for name in ['integrated','disconnected','validation']:
            self.assertEqual(v.config(repo,name),baseline)
        self.assertFalse(baseline['co2']['budget']['enable'])
        self.assertEqual(baseline['co2']['budget']['base_value'],1e9)

if __name__=='__main__':unittest.main(verbosity=2)
