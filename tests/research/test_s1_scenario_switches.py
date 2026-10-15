"""SYNTHETIC_TEST_ONLY: cross-border tagging/switches, transmission-limit parameter, cost scaling identity (S1-4, S1-6)."""
from pathlib import Path
import sys,unittest,hashlib,tempfile
import numpy as np,pandas as pd,pypsa
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
import scenario_network as sn
from s1_candidates import apply_cost_scaling,add_nuclear,add_site_candidates,confirm_extendable,PENDING

def network():
    n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=2,freq='3h'));n.snapshot_weightings.loc[:,:]=3.
    for b,c in [('SG0','SG'),('MY0','MY'),('MY1','MY')]:
        n.add('Bus',b,carrier='AC',v_nom=380.);n.buses.loc[b,'country']=c;n.add('Bus',b+' H2',carrier='H2');n.buses.loc[b+' H2','country']=c
    n.add('Carrier','AC');n.add('Carrier','DC');n.add('Carrier','H2 pipeline')
    n.add('Line','xb',bus0='SG0',bus1='MY0',carrier='AC',s_nom=525.,s_nom_min=525.,s_nom_extendable=True,length=240.,x=1.,r=.1,capital_cost=10.)
    n.add('Line','dom',bus0='MY0',bus1='MY1',carrier='AC',s_nom=100.,s_nom_min=100.,s_nom_extendable=True,length=50.,x=1.,r=.1,capital_cost=10.)
    n.add('Link','xb dc',bus0='MY1',bus1='SG0',carrier='DC',p_nom=300.,p_nom_min=300.,p_nom_extendable=True,length=130.,capital_cost=5.)
    n.add('Link','H2 pipeline SG0 -> MY0',bus0='SG0 H2',bus1='MY0 H2',carrier='H2 pipeline',p_nom_extendable=True,p_min_pu=-1,length=240.,capital_cost=1.)
    n.add('Link','H2 pipeline MY0 -> MY1',bus0='MY0 H2',bus1='MY1 H2',carrier='H2 pipeline',p_nom_extendable=True,p_min_pu=-1,length=50.,capital_cost=1.)
    n.add('GlobalConstraint','lv_limit',type='transmission_volume_expansion_limit',carrier_attribute='AC, DC',sense='<=',constant=1e6)
    n.meta={'required_constraint_hooks':[]}
    return n

def corridors():
    return pd.DataFrame([dict(component_type='Line',component='xb',capacity_2025_mw=525.,subsea_share=0.),dict(component_type='Link',component='xb dc',capacity_2025_mw=300.,subsea_share=0.)])

def costs():
    return pd.DataFrame({'FOM':[2.,2.,0.35,2.],'investment':[442.1414,442.1414,1008.2934,165000.]},index=['HVAC overhead','HVDC overhead','HVDC submarine','HVDC inverter pair'])

class Switches(unittest.TestCase):
    def test_tags_from_bus_country(self):
        n=network();s=sn.tag_cross_border(n)
        self.assertEqual(n.lines.border_class.tolist(),['cross_border','domestic']);self.assertEqual(n.links.loc['xb dc','border_class'],'cross_border');self.assertEqual(n.links.loc['H2 pipeline MY0 -> MY1','border_class'],'domestic')
        self.assertEqual(s['Link']['cross_border_by_carrier'],{'H2':1,'electricity':1})
    def test_disconnected_removes_cross_border_only(self):
        n=network();sn.tag_cross_border(n)
        led=sn.apply_cross_border_switches(n,dict(electricity=False,H2=False,gas=False,co2=False),corridors(),dict(fom_on_existing=True),costs())
        self.assertEqual(set(n.lines.index),{'dom'});self.assertEqual(set(n.links.index),{'H2 pipeline MY0 -> MY1'})
        self.assertEqual(led['electricity']['removed_count'],2);self.assertEqual(led['H2']['removed_count'],1);self.assertEqual(n.meta['existing_cross_border_fom_eur'],0.)
    def test_integrated_keeps_2025_lower_bound_and_books_fom_once(self):
        n=network();sn.tag_cross_border(n)
        led=sn.apply_cross_border_switches(n,dict(electricity=True,H2=True,gas=False,co2=False),corridors(),dict(fom_on_existing=True),costs())
        self.assertEqual(led['electricity']['kept'],2);self.assertEqual(n.lines.at['xb','s_nom_min'],525.)
        expected=.02*442.1414*240.*525.+(.02*442.1414*130.+.02*165000.)*300.
        self.assertAlmostEqual(n.meta['existing_cross_border_fom_eur'],expected,places=6);self.assertIn(sn.XB_FOM_HOOK,n.meta['required_constraint_hooks'])
        import linopy
        n.model=linopy.Model();n.model.add_variables(lower=0,name='dummy');n.model.add_objective(1.*n.model.variables['dummy'])
        sn.install_existing_cross_border_fom(n);self.assertIn('Research_existing_cross_border_FOM_constant',n.model.variables)
        with self.assertRaisesRegex(ValueError,'already'):sn.install_existing_cross_border_fom(n)
    def test_corridor_table_mismatch_rejected(self):
        n=network();sn.tag_cross_border(n)
        with self.assertRaisesRegex(ValueError,'corridor'):sn.apply_cross_border_switches(n,dict(electricity=True,H2=True,gas=False,co2=False),corridors().iloc[:1],dict(fom_on_existing=False),costs())
    def test_missing_lower_bound_rejected(self):
        n=network();sn.tag_cross_border(n);n.lines.at['xb','s_nom_min']=0.
        with self.assertRaisesRegex(ValueError,'lower bound'):sn.apply_cross_border_switches(n,dict(electricity=True,H2=True,gas=False,co2=False),corridors(),dict(fom_on_existing=False),costs())
    def test_transmission_limit_modes(self):
        n=network();r=sn.set_transmission_limit(n,dict(volume_limit_mode='inherit_reference_constant',volume_limit_factor=2.))
        self.assertEqual(r['constant_mwkm'],1e6);self.assertEqual(n.global_constraints.at['lv_limit','constant'],1e6)
        r=sn.set_transmission_limit(n,dict(volume_limit_mode='factor_of_existing',volume_limit_factor=2.))
        self.assertAlmostEqual(r['constant_mwkm'],2*(525*240+100*50+300*130));self.assertAlmostEqual(n.global_constraints.at['lv_limit','constant'],r['constant_mwkm'])
        with self.assertRaises(ValueError):sn.set_transmission_limit(n,dict(volume_limit_mode='other'))
    def test_rename_legacy_buses(self):
        n=pypsa.Network();n.add('Bus','TH2 0 :: gas',carrier='gas');n.add('Bus','TH2 0',carrier='AC');n.add('Link','x',bus0='TH2 0 :: gas',bus1='TH2 0')
        m=sn.rename_legacy_buses(n);self.assertEqual(m,{'TH2 0 :: gas':'TH2 0 gas'});self.assertEqual(n.links.at['x','bus0'],'TH2 0 gas');self.assertIn('TH2 0 gas',n.buses.index)

class CostScaling(unittest.TestCase):
    def test_factor_one_is_bit_identical_and_existing_untouched(self):
        n=network();n.add('Carrier','nuclear');n.add('Generator','g',bus='SG0',carrier='nuclear',p_nom_extendable=True,capital_cost=654653.6157847332)
        n.add('Generator','old',bus='SG0',carrier='nuclear',p_nom=1.,capital_cost=0.);n.generators.loc['old','asset_role']='existing_survivor';n.generators.loc['g','asset_role']='new_build_candidate'
        before=n.generators.capital_cost.to_numpy().copy()
        led=apply_cost_scaling(n,{'nuclear':1.0});self.assertTrue(np.array_equal(before.view('<u8'),n.generators.capital_cost.to_numpy().view('<u8')));self.assertFalse(led[0]['applied'])
        apply_cost_scaling(n,{'nuclear':1.5});self.assertAlmostEqual(n.generators.at['g','capital_cost'],654653.6157847332*1.5);self.assertEqual(n.generators.at['old','capital_cost'],0.)
        with self.assertRaises(ValueError):apply_cost_scaling(n,{'nuclear':-1.})

class Candidates(unittest.TestCase):
    def costs(self):
        return pd.DataFrame({'fixed':[654653.6,217095.6,116604.1,125242.2,182698.7],'marginal_cost':[12.57,.263,.439,.526,0.],'efficiency':[.326,1.,.9,.9,.75],'lifetime':[40.,30.,80.,80.,80.]},index=['nuclear','geothermal','ror','hydro','PHS'])
    def test_siting_table_and_smr_pending(self):
        n=network();cfg=dict(evidence_grade='C',large_pwr=dict(carrier='nuclear',cost_technology='nuclear',allowed_countries=['MY']),smr=dict(carrier='nuclear SMR',cost_technology=None,allowed_countries=['SG','MY'],p_nom_max=0.,status='DATA_PENDING'))
        led=add_nuclear(n,self.costs(),cfg,['SG0','MY0','MY1'])
        self.assertNotIn('SG0 nuclear',n.generators.index);self.assertIn('MY0 nuclear',n.generators.index);self.assertEqual(n.generators.at['MY0 nuclear','capital_cost'],654653.6)
        self.assertEqual(n.generators.at['SG0 nuclear SMR','p_nom_max'],0.);self.assertEqual(n.generators.at['SG0 nuclear SMR','cost_qualification'],PENDING);self.assertEqual(n.generators.at['MY0 nuclear','siting_evidence_grade'],'C')
        self.assertEqual(len(led),5)
    def test_site_candidates_zero_potential(self):
        n=network();cfg=dict(geothermal=dict(carrier='geothermal',component='Generator',cost_technology='geothermal',p_nom_max=0.,status='DATA_PENDING'),PHS_new=dict(carrier='PHS',component='StorageUnit',cost_technology='PHS',p_nom_max=0.,status='DATA_PENDING'),hydro_new=dict(carrier='hydro',component='StorageUnit',cost_technology='hydro',p_nom_max=0.,status='DATA_PENDING'))
        led=add_site_candidates(n,self.costs(),cfg,['SG0'],dict(PHSMaxHours=6,DecisionReference='GATE4-20261005-HYDRO-PHYSICAL-POLICY-SEPARATION'))
        self.assertEqual(n.generators.at['SG0 geothermal','p_nom_max'],0.);self.assertEqual(n.storage_units.at['SG0 PHS_new','max_hours'],6.);self.assertEqual(n.storage_units.at['SG0 hydro_new','max_hours'],0.)
        self.assertTrue(all(r['status']==PENDING for r in led))
    def test_confirm_extendable(self):
        n=network();n.add('Carrier','H2 turbine');n.add('Link','t',bus0='SG0 H2',bus1='SG0',carrier='H2 turbine',p_nom_extendable=True,capital_cost=1.)
        self.assertEqual(confirm_extendable(n,['H2 turbine'])['H2 turbine']['count'],1)
        n.links.at['t','p_nom_extendable']=False
        with self.assertRaises(ValueError):confirm_extendable(n,['H2 turbine'])
        with self.assertRaises(ValueError):confirm_extendable(n,['missing carrier'])
if __name__=='__main__':unittest.main()
