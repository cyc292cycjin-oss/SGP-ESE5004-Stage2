"""SYNTHETIC_TEST_ONLY: upstream adapter import/injection, exact daily reduction, V5 B-gate logic, stock re-run."""
from pathlib import Path
import sys,unittest,json
import numpy as np,pandas as pd,pypsa
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
import sector_adapter as sa
from daily_resolution import to_daily,average
from v5 import v5_gates as g
from assembly_components import register_upstream_loads

class Adapter(unittest.TestCase):
    def test_upstream_imports_and_not_called_list_exists(self):
        psn=sa.load_upstream(ROOT)
        for name in sa.NOT_CALLED:self.assertTrue(callable(getattr(psn,name)))
        self.assertTrue(callable(psn.add_hydrogen));self.assertTrue(callable(psn.define_spatial))
    def test_inject_records_every_global(self):
        psn=sa.load_upstream(ROOT);n=pypsa.Network();n.add('Bus','SG0',carrier='AC',x=103.8,y=1.3);n.buses.loc['SG0','country']='SG'
        from phase4_static import config
        cfg=config(ROOT,'baseline');options=sa.build_options(cfg['sector'],cfg['research']['hydrogen'])
        import tempfile
        rec=sa.inject(psn,n,options,['SG0'],{'SG'},Path(tempfile.mkdtemp())/'p.csv','AEO8_BAS')
        self.assertEqual(set(rec['injected']),set(sa.INJECTED_GLOBALS));self.assertEqual(rec['hydrogen_options']['network_routes'],'greenfield');self.assertFalse(rec['hydrogen_options']['gas_network_repurposing'])
        self.assertEqual(list(psn.spatial.nodes),['SG0']);self.assertEqual(psn.snakemake.params.sector_options['hydrogen']['production_technologies'],['H2 Electrolysis'])
    def test_spatial_nodes_and_dc_map(self):
        n=pypsa.Network()
        for b,c in [('A','AC'),('D1','DC'),('D2','DC')]:n.add('Bus',b,carrier=c)
        n.add('Link','conv',bus0='D1',bus1='A',carrier='B2B',p_nom=1.)
        self.assertEqual(sa.spatial_nodes(n),['A','D2']);self.assertEqual(sa.dc_to_ac(n),{'D1':'A'})
    def test_register_upstream_loads_once(self):
        n=pypsa.Network();n.set_snapshots(pd.Index(['t0'],name='snapshot'));n.add('Bus','SG0 H2',carrier='H2');n.buses.loc['SG0 H2','country']='SG';n.add('Load','SG0 H2 demand',bus='SG0 H2',carrier='H2',p_set=1.)
        n.meta={}
        register_upstream_loads(n,['SG0 H2 demand'],'add_hydrogen','HydrogenUpstream');self.assertEqual(n.meta['demand_owners']['SG0 H2 demand'],'UPSTREAM:add_hydrogen:SG0 H2 demand')
        with self.assertRaisesRegex(ValueError,'twice'):register_upstream_loads(n,['SG0 H2 demand'],'add_hydrogen','HydrogenUpstream')

class Daily(unittest.TestCase):
    def test_average_exact_and_constant_fast_path(self):
        a=np.arange(2920,dtype='<f8')/7.;d=average(a)
        self.assertEqual(d.shape,(365,));self.assertAlmostEqual(d.sum()*24,a.sum()*3,places=6)
        self.assertTrue(np.array_equal(average(np.full(2920,.3)),np.full(365,.3)))
        with self.assertRaises(ValueError):average(np.ones(100))
    def test_to_daily_conserves_integrals_and_statics(self):
        n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=2920,freq='3h',name='snapshot'));n.snapshot_weightings.loc[:,:]=3.
        n.add('Bus','SG0',carrier='AC');n.add('Load','l',bus='SG0',p_set=np.random.RandomState(1).rand(2920));n.add('Generator','g',bus='SG0',p_nom=5.,p_max_pu=np.random.RandomState(2).rand(2920));n.meta={'x':1}
        d,ledger=to_daily(n)
        self.assertEqual(len(d.snapshots),365);self.assertTrue((d.snapshot_weightings==24.).all().all())
        self.assertAlmostEqual(float(d.loads_t.p_set['l'].sum()*24),float(n.loads_t.p_set['l'].sum()*3),places=6);self.assertEqual(len(ledger),2);self.assertEqual(d.meta['temporal_resolution'],'365x24h')
        pd.testing.assert_frame_equal(n.generators,d.generators)

class DailyStoreBounds(unittest.TestCase):
    """V3 supplement 07 (decision 182): Store e_min_pu daily max, e_max_pu daily min (upstream average_every_nhours); every other series and every network without such bounds as before."""
    @staticmethod
    def _to_daily_before_182(n):   # the aggregation of to_daily at 2548123a without its input checks (every series the exact daily mean): the reference for "as before"
        from fractions import Fraction as F;import copy
        DAYS,PER_DAY=365,8
        expected=pd.date_range('2013-01-01',periods=DAYS*PER_DAY,freq='3h',name='snapshot')
        days=pd.DatetimeIndex(expected[::PER_DAY].values,name='snapshot')
        frames={};ledger=[]
        for c in n.iterate_components():
            for attr,frame in c.pnl.items():
                if not len(frame.columns):continue
                result=np.empty((DAYS,len(frame.columns)),dtype='<f8')
                for i,name in enumerate(frame.columns):result[:,i]=average(frame[name].to_numpy())
                frames[c.name,attr]=pd.DataFrame(result,index=days,columns=frame.columns)
        out=n.copy();out.meta=copy.deepcopy(n.meta)
        out.set_snapshots(days)
        out.snapshot_weightings.loc[:,['objective','generators','stores']]=24.
        for (c,a),frame in frames.items():out.pnl(c)[a]=frame
        out.meta.update(temporal_resolution='365x24h',temporal_reduction='S1 exact daily mean of frozen 2920x3h inputs (C02 arithmetic)',parent_resolution='2920x3h')
        return out,ledger
    @staticmethod
    def _net(bounds):
        n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=2920,freq='3h',name='snapshot'));n.snapshot_weightings.loc[:,:]=3.
        n.add('Bus','SG0',carrier='AC');n.add('Bus','SG0 EV battery',carrier='Li ion')
        n.add('Load','l',bus='SG0',p_set=np.random.RandomState(1).rand(2920));n.add('Generator','g',bus='SG0',p_nom=5.,p_max_pu=np.random.RandomState(2).rand(2920))
        n.add('Link','charger',bus0='SG0',bus1='SG0 EV battery',p_nom=1.,efficiency=.9,p_max_pu=.7+.1*np.random.RandomState(3).rand(2920))
        n.add('Load','ev',bus='SG0 EV battery',p_set=.2*np.random.RandomState(4).rand(2920))
        if bounds:   # as v3_layers.apply_ev_structure: 0.8 in the one 3 h slot of the local morning (UTC 00-03 for +6.5 / +7, 21-24 for +8 / +9), 0 otherwise
            for k,slot in enumerate((0,7)):
                e=np.zeros(2920);e[slot::8]=.8;n.add('Store',f'ev battery {k}',bus='SG0 EV battery',e_nom=1.,e_cyclic=True,e_min_pu=e)
            n.add('Store','capped',bus='SG0 EV battery',e_nom=1.,e_max_pu=1.-.3*np.random.RandomState(5).rand(2920))
        n.add('Store','plain',bus='SG0 EV battery',e_nom=2.,e_cyclic=True)
        n.meta={'x':1};return n
    def test_ev_morning_floor_is_the_daily_max(self):
        n=self._net(True);d,ledger=to_daily(n)
        lo=d.stores_t.e_min_pu;self.assertEqual(sorted(lo.columns),['ev battery 0','ev battery 1']);self.assertEqual(lo.shape,(365,2))
        self.assertTrue((lo.to_numpy()==.8).all())   # 0.8 every day, not the mean 0.1
        hi=n.stores_t.e_max_pu['capped'].to_numpy().reshape(365,8).min(axis=1);self.assertTrue(np.array_equal(d.stores_t.e_max_pu['capped'].to_numpy(),hi))
        m={(r['component'],r['attribute']):r['method'] for r in ledger}
        self.assertIn('daily max',m['Store','e_min_pu']);self.assertIn('daily min',m['Store','e_max_pu']);self.assertTrue(m['Load','p_set'].startswith('exact rational mean'))
    def test_store_bounds_equal_upstream_average_every_nhours(self):
        n=self._net(True);d,_=to_daily(n);up=sa.load_upstream(ROOT).average_every_nhours(n,'24h')
        for a in ('e_min_pu','e_max_pu'):
            self.assertTrue(np.array_equal(d.stores_t[a].to_numpy(),up.stores_t[a][d.stores_t[a].columns].to_numpy()),a)
    def test_every_other_series_as_before(self):
        n=self._net(True);d,_=to_daily(n);old,_=self._to_daily_before_182(n);seen=0
        for c in n.iterate_components():
            for attr,frame in c.pnl.items():
                if not len(frame.columns) or (c.list_name=='stores' and attr in ('e_min_pu','e_max_pu')):continue
                a,b=d.pnl(c.name)[attr].to_numpy(dtype='<f8'),old.pnl(c.name)[attr].to_numpy(dtype='<f8');seen+=1
                self.assertTrue(np.array_equal(a.view('<u8'),b.view('<u8')),c.name+'.'+attr)
        self.assertEqual(seen,3);self.assertEqual(d.meta,old.meta)
        for c in n.iterate_components():pd.testing.assert_frame_equal(d.df(c.name),old.df(c.name),check_exact=True)
    def test_network_without_store_bounds_byte_identical(self):
        import tempfile
        n=self._net(False);t=Path(tempfile.mkdtemp());d,_=to_daily(n);old,_=self._to_daily_before_182(n)
        d.export_to_netcdf(t/'new.nc');old.export_to_netcdf(t/'old.nc')
        self.assertEqual((t/'new.nc').read_bytes(),(t/'old.nc').read_bytes())

class GatesB(unittest.TestCase):
    def test_b5_config_diff_only_switches(self):
        a={'research':{'scenario':'integrated','cross_border':{'electricity':True,'H2':True,'gas':True,'co2':True},'x':1}}
        b={'research':{'scenario':'disconnected','cross_border':{'electricity':False,'H2':False,'gas':False,'co2':False},'x':1}}
        self.assertTrue(g.gate_b5_single_switch(a,b)['passed'])
        b['research']['x']=2;self.assertFalse(g.gate_b5_single_switch(a,b)['passed'])
    def test_b5_disconnected_zero_capacity(self):
        a={'research':{'scenario':'integrated','cross_border':{'electricity':True,'H2':True,'gas':True,'co2':True}}};b={'research':{'scenario':'disconnected','cross_border':{'electricity':False,'H2':False,'gas':False,'co2':False}}}
        n=pypsa.Network();n.set_snapshots(pd.Index(['t0'],name='snapshot'));n.add('Bus','A');n.add('Bus','B');n.add('Line','x',bus0='A',bus1='B',s_nom=1.,x=1.,r=1.);n.lines['border_class']='domestic';n.lines['s_nom_opt']=1.;n.links['border_class']=[];n.lines_t['p0']=pd.DataFrame({'x':[0.]},index=n.snapshots)
        self.assertTrue(g.gate_b5_single_switch(a,b,n_dis_solved=n)['passed'])
        n.lines['border_class']='cross_border';self.assertFalse(g.gate_b5_single_switch(a,b,n_dis_solved=n)['passed'])
    def test_b6(self):
        self.assertTrue(g.gate_b6_cost(100.,100.)['passed']);self.assertTrue(g.gate_b6_cost(99.,100.)['passed']);self.assertFalse(g.gate_b6_cost(101.,100.)['passed'])
    def test_b12_hash(self):
        cfg={'research':{'scenario':'integrated','cross_border':{'electricity':True,'H2':True,'gas':True,'co2':True}}}
        n=pypsa.Network();n.meta={'research_config_sha256':g.config_sha(cfg['research']),'scenario':'integrated','research_cross_border':{'switches':cfg['research']['cross_border']},'skeleton_status':'INTERIM_S1_SKELETON'}
        self.assertTrue(g.gate_b12_hash(n,cfg)['passed']);n.meta['scenario']='other';self.assertFalse(g.gate_b12_hash(n,cfg)['passed'])
    def test_contract_loads(self):
        c=g.load_contract();self.assertEqual(c['contract_id'],'RESEARCH_V5_SKELETON');self.assertFalse(c['approved_by_user'])

class StockReview(unittest.TestCase):
    def test_geothermal_rerun_30y(self):
        from s1_inputs_review import rerun_geothermal
        unit=dict(AssetID='GEM:x',RawUnitID='x',ParentAssetID='PPM:1',Country='ID',Technology='Geothermal',OriginalCapacity=50,CommissioningYear=2021,RetirementYear=None,CommissioningEvidenceVerified=True,RetirementEvidenceVerified=False,AssetClass='OBSERVED_EXISTING',Lifetime=15,LifetimeAccepted=True,CapacityReconciliation='MATCHED_PARENT',SurvivalStatus='NOT_ACTIVE_2050',RetainedCapacity2050=0.,ConditionalCapacityQualified=True)
        stock={'unit_evidence':{'records':[unit,dict(unit,AssetID='GEM:y',Technology='Hydro')]}}
        dec=json.loads((ROOT/'research_inputs/asset_survival/lifetime_decisions_s1.json').read_text())
        new,tr=rerun_geothermal(stock,dec)
        self.assertEqual(tr[0]['After'],'SURVIVES_2050');self.assertEqual(tr[0]['RetainedMW2050'],50.);self.assertEqual(new['unit_evidence']['records'][1]['SurvivalStatus'],'NOT_ACTIVE_2050');self.assertEqual(new['unit_evidence']['records'][0]['Lifetime'],30)
if __name__=='__main__':unittest.main()
