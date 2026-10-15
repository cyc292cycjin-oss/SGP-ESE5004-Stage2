"""Integration checks on the actual S1 scenario networks (skipped until they are built). No solver."""
from pathlib import Path
import sys,unittest,json
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
S1=ROOT/'results_project/s1'

def built(scenario):return (S1/scenario/f'{scenario}_BUILD_RECEIPT.json').exists() and (S1/scenario/f'{scenario}_2920_3h_unsolved.nc').exists()

@unittest.skipUnless(built('integrated') and built('disconnected'),'S1 scenario networks not built')
class BuiltNetworks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pypsa,logging
        logging.disable(logging.CRITICAL)
        from phase4_static import config
        cls.n={s:pypsa.Network(str(S1/s/f'{s}_2920_3h_unsolved.nc')) for s in ['integrated','disconnected']}
        cls.cfg={s:config(ROOT,s) for s in ['integrated','disconnected']}
        cls.receipt={s:json.loads((S1/s/f'{s}_BUILD_RECEIPT.json').read_text()) for s in ['integrated','disconnected']}
        cls.corridors=pd.read_csv(ROOT/'research_inputs/corridors/cross_border_corridors.csv',float_precision='round_trip')
    def test_static_validation_passes_on_reload(self):
        from build_research_network import static_validate_s1
        for s,n in self.n.items():
            r=static_validate_s1(n,self.cfg[s],self.corridors);self.assertEqual(r['status'],'S1_STATIC_PASS',s)
    def test_disconnected_has_no_cross_border_components(self):
        n=self.n['disconnected']
        self.assertEqual(int((n.lines.border_class=='cross_border').sum()),0);self.assertEqual(int((n.links.border_class=='cross_border').sum()),0)
        self.assertEqual(self.receipt['disconnected']['cross_border']['electricity']['removed_count'],24)
    def test_integrated_keeps_24_edges_with_lower_bound(self):
        n=self.n['integrated'];xb=n.lines[n.lines.border_class=='cross_border'];xl=n.links[(n.links.border_class=='cross_border')&(n.links.transport_carrier=='electricity')]
        self.assertEqual(len(xb)+len(xl),24);self.assertTrue((xb.s_nom_min==xb.s_nom).all() or np.allclose(xb.s_nom_min,xb.s_nom));self.assertTrue(xb.s_nom_extendable.all() and xl.p_nom_extendable.all())
        self.assertGreater(n.meta['existing_cross_border_fom_eur'],0.);self.assertIn('research_cross_border_existing_fom',n.meta['required_constraint_hooks'])
    def test_scenarios_differ_only_by_switch_set(self):
        from v5.v5_gates import gate_b5_single_switch
        self.assertTrue(gate_b5_single_switch(self.cfg['integrated'],self.cfg['disconnected'])['passed'])
        a,b=self.n['integrated'],self.n['disconnected']
        # same generators, stores, loads, buses; only transport edges differ
        for typ in ['Generator','Store','StorageUnit','Load','Bus']:self.assertEqual(set(a.df(typ).index),set(b.df(typ).index),typ)
        self.assertEqual(set(a.lines.index)-set(b.lines.index),set(a.lines.index[a.lines.border_class=='cross_border']))
    def test_country_atmosphere_and_u4(self):
        from country_carbon import validate_country_attribution
        for s,n in self.n.items():
            r=validate_country_attribution(n);self.assertEqual(r['atmosphere_buses'],11);self.assertEqual(set(r['ports_by_country']),set(n.buses.country[n.buses.carrier=='AC'].unique()))
            self.assertTrue((n.carriers.co2_emissions==0).all())
    def test_demand_is_astar_only(self):
        for s,n in self.n.items():
            self.assertTrue((n.loads.account=='Astar').all());self.assertEqual(len(n.loads),self.receipt[s]['demand']['loads']);self.assertEqual(len(n.loads),96);  # 4 converter-side DC buses carry zero Astar demand
            self.assertAlmostEqual(self.receipt[s]['demand']['total_twh'],2617.7602787505957,places=3)
    def test_nuclear_siting(self):
        n=self.n['integrated'];g=n.generators
        self.assertEqual(set(g.country[g.carrier=='nuclear']),set('BN KH ID LA MY MM PH TH TL VN'.split()));self.assertNotIn('SG',set(g.country[g.carrier=='nuclear']))
        self.assertIn('SG',set(g.country[g.carrier=='nuclear SMR']));self.assertTrue((g.p_nom_max[g.carrier=='nuclear SMR']==0).all())
    def test_upstream_h2_components(self):
        n=self.n['integrated']
        for carrier,typ in [('H2 Electrolysis','Link'),('H2 Fuel Cell','Link'),('H2 turbine','Link'),('H2 Store Tank','Store'),('H2 pipeline','Link')]:
            df=n.df(typ);self.assertGreater(int((df.carrier==carrier).sum()),0,carrier)
        self.assertFalse(any(' :: ' in b for b in n.buses.index))
    def test_daily_network_weights(self):
        import pypsa
        for s in ['integrated','disconnected']:
            d=pypsa.Network(str(S1/s/f'{s}_365_24h_unsolved.nc'));self.assertEqual(len(d.snapshots),365);self.assertTrue((d.snapshot_weightings.sum()==8760).all())
if __name__=='__main__':unittest.main()
