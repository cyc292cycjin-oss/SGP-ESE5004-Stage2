import sys,unittest
from pathlib import Path
import numpy as np
import pandas as pd
import pypsa
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts_project'))
from validation_temporal import daily_validation_network

class TemporalTests(unittest.TestCase):
    def fixture(self):
        n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=2920,freq='3h',name='snapshot'));n.snapshot_weightings.loc[:,:]=3.
        n.add('Bus','SG input',country='SG',carrier='AC');x=np.arange(2920,dtype=float)%8+1.
        for i in range(171):
            n.add('Load',str(i),bus='SG input',p_set=x+i);n.loads.loc[str(i),'source_account_id']='account'+str(i)
        n.add('Generator','solar',bus='SG input',p_nom_extendable=True,capital_cost=5,p_max_pu=x/8)
        n.add('StorageUnit','hydro',bus='SG input',p_nom=100,max_hours=6,inflow=x*3)
        n.meta=dict(artifact_role='FULL_SC_RESEARCH_BASELINE_UNSOLVED',fullsc_network_complete=True,policy_enabled=False,solver_allowed=False)
        return n
    def test_daily_preserves_all_energy_and_inputs(self):
        n=self.fixture();before=n.loads_t.p_set.copy();r,checks=daily_validation_network(n)
        self.assertEqual(len(r.snapshots),365);self.assertEqual(len(n.snapshots),2920);self.assertEqual(len(r.loads),171)
        pd.testing.assert_frame_equal(n.loads_t.p_set,before);pd.testing.assert_frame_equal(n.generators,r.generators)
        self.assertTrue(all(x['Status']=='PASS' for x in checks));self.assertFalse(n.meta['solver_allowed']);self.assertTrue(r.meta['solver_allowed']);self.assertFalse(r.meta['scientific_results_allowed'])
        self.assertAlmostEqual(float(r.storage_units_t.inflow.sum().sum()*24),float(n.storage_units_t.inflow.sum().sum()*3))
    def test_unknown_aggregation_semantics_rejected(self):
        n=self.fixture();n.generators_t.efficiency['solar']=np.linspace(.5,.8,2920)
        with self.assertRaisesRegex(ValueError,'explicit aggregation'):daily_validation_network(n)
    def test_diagnostic_and_policy_on_rejected(self):
        n=self.fixture();n.meta['artifact_role']='DIAGNOSTIC_PARTIAL_UNSOLVED'
        with self.assertRaisesRegex(ValueError,'complete frozen'):daily_validation_network(n)
        n=self.fixture();n.meta['policy_enabled']=True
        with self.assertRaisesRegex(ValueError,'OFF'):daily_validation_network(n)
if __name__=='__main__':unittest.main()
