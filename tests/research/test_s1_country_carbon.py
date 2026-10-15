"""SYNTHETIC_TEST_ONLY: per-country atmosphere accounting (S1-5). No solver; a small linopy model tests the hook."""
from pathlib import Path
import sys,unittest
import numpy as np,pandas as pd,pypsa,linopy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
import country_carbon as cc
from carrier_architecture import atmosphere_bus,ATMOSPHERE_CARRIER,LEGACY_ATMOSPHERE,COUNTRIES

def network():
    n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=3,freq='3h'));n.snapshot_weightings.loc[:,:]=3.
    for b,c in [('SG0','SG'),('MY0','MY')]:
        n.add('Bus',b,carrier='AC');n.buses.loc[b,'country']=c
        n.add('Bus',b+' gas',carrier='gas');n.buses.loc[b+' gas','country']=c
    n.add('Carrier','gas',co2_emissions=0.198);n.add('Carrier','OCGT');n.add('Carrier',ATMOSPHERE_CARRIER,co2_emissions=0.)
    n.add('Bus',LEGACY_ATMOSPHERE,carrier=ATMOSPHERE_CARRIER);n.buses.loc[LEGACY_ATMOSPHERE,'country']=''
    n.add('Store',LEGACY_ATMOSPHERE+' inventory',bus=LEGACY_ATMOSPHERE,carrier=ATMOSPHERE_CARRIER,e_nom_extendable=True,e_min_pu=-1)
    for b in ['SG0','MY0']:
        n.add('Link',b+' OCGT',bus0=b+' gas',bus1=b,bus2=LEGACY_ATMOSPHERE,efficiency=.4,efficiency2=.198,p_nom_extendable=True)
        n.add('Generator',b+' gas supply',bus=b+' gas',carrier='gas',p_nom_extendable=True)
    return n

class CountryCarbon(unittest.TestCase):
    def test_reconnect_books_each_emitter_in_its_own_country(self):
        n=network();cc.add_country_atmosphere(n,{'SG','MY'});moves=cc.reconnect_atmosphere_ports(n)
        self.assertEqual(n.links.at['SG0 OCGT','bus2'],atmosphere_bus('SG'));self.assertEqual(n.links.at['MY0 OCGT','bus2'],atmosphere_bus('MY'))
        self.assertNotIn(LEGACY_ATMOSPHERE,n.buses.index);self.assertEqual(sum(m['component_type']=='Link' for m in moves),2)
    def test_u4_zeroes_carrier_intensity(self):
        n=network();self.assertEqual(cc.fix_u4(n),['gas']);self.assertEqual(n.carriers.at['gas','co2_emissions'],0.)
    def test_registry_once_and_foreign_atmosphere_rejected(self):
        n=network();cc.add_country_atmosphere(n,{'SG','MY'});cc.reconnect_atmosphere_ports(n);cc.fix_u4(n)
        reg=cc.emission_registry(n);self.assertEqual({r['component'] for r in reg},{'SG0 OCGT','MY0 OCGT'});self.assertTrue(all(r['direction']=='EMISSION' for r in reg))
        n.links.at['SG0 OCGT','bus2']=atmosphere_bus('MY')
        with self.assertRaisesRegex(ValueError,'foreign'):cc.emission_registry(n)
    def test_validate_requires_all_11_and_zero_generator_intensity(self):
        n=network();cc.add_country_atmosphere(n);cc.reconnect_atmosphere_ports(n)
        with self.assertRaisesRegex(ValueError,'U4'):cc.validate_country_attribution(n)
        cc.fix_u4(n);r=cc.validate_country_attribution(n);self.assertEqual(r['atmosphere_buses'],11);self.assertEqual(r['emission_ports'],2)
    def test_hook_adds_one_constraint_per_country_on_last_snapshot(self):
        n=network();cc.add_country_atmosphere(n);cc.reconnect_atmosphere_ports(n);cc.fix_u4(n)
        cfg=dict(constraint_scope='per_country',country_cap_tco2={c:0. for c in COUNTRIES},asean_total_cap_tco2=0.)
        cc.install_metadata(n,cfg);self.assertIn(cc.HOOK,n.meta['required_constraint_hooks'])
        n.model=linopy.Model();n.model.add_variables(coords=[n.snapshots,pd.Index(n.stores.index,name='Store')],name='Store-e')
        cc.add_country_net_zero(n,n.snapshots)
        names=[k for k in n.model.constraints if k.startswith('research_country_co2_limit-')]
        self.assertEqual(len(names),11)
        con=n.model.constraints['research_country_co2_limit-SG']
        self.assertTrue((con.sign.values=='<=').all());self.assertEqual(float(con.rhs.values),0.)
        with self.assertRaisesRegex(ValueError,'already'):cc.add_country_net_zero(n,n.snapshots)
    def test_asean_total_scope_is_one_constraint(self):
        n=network();cc.add_country_atmosphere(n);cc.reconnect_atmosphere_ports(n);cc.fix_u4(n)
        cc.install_metadata(n,dict(constraint_scope='asean_total',country_cap_tco2={c:0. for c in COUNTRIES},asean_total_cap_tco2=5.))
        n.model=linopy.Model();n.model.add_variables(coords=[n.snapshots,pd.Index(n.stores.index,name='Store')],name='Store-e')
        cc.add_country_net_zero(n,n.snapshots);self.assertIn('research_asean_co2_limit',n.model.constraints);self.assertEqual(float(n.model.constraints['research_asean_co2_limit'].rhs.values),5.)
    def test_metadata_rejects_incomplete_caps_or_unknown_scope(self):
        n=network()
        with self.assertRaises(ValueError):cc.install_metadata(n,dict(constraint_scope='per_country',country_cap_tco2={'SG':0.},asean_total_cap_tco2=0.))
        with self.assertRaises(ValueError):cc.install_metadata(n,dict(constraint_scope='global',country_cap_tco2={c:0. for c in COUNTRIES},asean_total_cap_tco2=0.))
if __name__=='__main__':unittest.main()
