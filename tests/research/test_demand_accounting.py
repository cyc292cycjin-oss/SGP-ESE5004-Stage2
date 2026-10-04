"""Static contracts, mutation tests, and pinned-input integration; no optimize."""
from pathlib import Path
import copy,hashlib,json,math,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
import demand_accounting as a
from demand_sources import row,load_sources


def accepted(account='Fuel',carrier='oil',value=100):
    return row('SG',2019,'Transport',account,carrier,ConvertedMWh=value,RawValue=value,RawUnit='MWh/year',
               Source='SYNTHETIC_TEST_ONLY',SourceSHA256='1'*64,NumericAccepted=True,Status='HUMAN_ACCEPTED',
               HumanAcceptance='VALUE_AND_ASTAR_MEMBERSHIP_ACCEPTED',ZeroEvidence='REPORTED_VALUE')


class DemandTests(unittest.TestCase):
    def test_units(self):
        self.assertEqual(a.convert('1','Kilowatt-hours, million'),1000)
        self.assertEqual(a.convert('1','TWh/year'),1e6)
        self.assertAlmostEqual(a.convert('3.6','Terajoules'),1000)
    def test_mass_unit_requires_calorific_evidence(self):
        with self.assertRaises(ValueError):a.convert(3,'tonnes')
    def test_unknown_nonfinite_negative(self):
        for x in [None,'',float('nan'),float('inf'),-1,True]:
            with self.subTest(value=x),self.assertRaises(ValueError):a.energy(x)
    def test_reported_zero(self):
        r=accepted(value=0);r['ZeroEvidence']='REPORTED_ZERO';self.assertEqual(a.validate_ledger([r]),[])
    def test_not_applicable_zero(self):
        r=accepted(value=0);r['ZeroEvidence']='NOT_APPLICABLE';self.assertEqual(a.validate_ledger([r]),[])
    def test_unsupported_zero(self):
        with self.assertRaises(ValueError):a.validate_ledger([accepted(value=0)])
    def test_ledger_nan_inf_negative(self):
        for x in [float('nan'),float('inf'),-1]:
            with self.subTest(value=x),self.assertRaises(ValueError):a.validate_ledger([accepted(value=x)])
    def test_duplicate_identity(self):
        r=accepted()
        with self.assertRaises(ValueError):a.validate_ledger([r,r])
    def test_duplicate_owner(self):
        r=accepted();s=copy.deepcopy(r);s['RowID']='other'
        with self.assertRaises(ValueError):a.validate_ledger([r,s])
    def test_wrong_country(self):
        r=accepted();r['Country']='XX'
        with self.assertRaises(ValueError):a.validate_ledger([r])
    def test_embedded_conflict(self):
        r=accepted();r['Representation']='EMBEDDED'
        with self.assertRaises(ValueError):a.validate_ledger([r])
    def test_astar_duplicate(self):
        r=accepted(carrier='electricity');r['IncludedInAstar']=True
        with self.assertRaises(ValueError):a.validate_ledger([r])
    def test_endogenous_fixed_conflict(self):
        r=accepted();r['DemandType']='ENDOGENOUS_CONVERSION_INPUT'
        with self.assertRaises(ValueError):a.validate_ledger([r])
    def test_conversion_in_astar_conflict(self):
        r=accepted();r.update(DemandType='ENDOGENOUS_CONVERSION_INPUT',ConvertedMWh=None,FixedOrEndogenous='ENDOGENOUS',Posting=False,IncludedInAstar=True)
        with self.assertRaises(ValueError):a.validate_ledger([r])
    def test_bunker_domestic_conflict(self):
        r=accepted();r['DemandType']='BUNKER_FUEL'
        with self.assertRaises(ValueError):a.validate_ledger([r])
    def test_emissions_not_energy(self):
        r=accepted('IndustryFuel','coal');r.update(EmissionsPresent=True,ExistingEnergyLoad=False)
        self.assertIn((r['RowID'],'MISSING_ENERGY_OBLIGATION'),a.validate_ledger([r]))
    def test_missing_destination_flag(self):
        r=accepted();r['LogicalDestination']=''
        self.assertIn((r['RowID'],'NO_VALID_CARRIER_DESTINATION'),a.validate_ledger([r]))
    def test_missing_annual_not_zero(self):
        r=accepted();r.update(ConvertedMWh=None,NumericAccepted=False,Status='MISSING')
        self.assertIn((r['RowID'],'MISSING_ANNUAL_DATA'),a.validate_ledger([r]))
    def test_transfer_independent(self):
        p=a.parent_transfer(100,[('industry',30),('EV',5)],100,accepted=True)
        self.assertEqual(p['ParentAfter'],65);self.assertEqual(p['TransferredChild'],35)
    def test_transfer_no_child_keeps_parent(self):
        self.assertEqual(a.parent_transfer(100,[],100,accepted=True)['ParentAfter'],100)
    def test_transfer_bad_reference(self):
        with self.assertRaises(ValueError):a.parent_transfer(100,[('a',10)],99,accepted=True)
    def test_transfer_duplicate(self):
        with self.assertRaises(ValueError):a.parent_transfer(100,[('a',10),('a',10)],100,accepted=True)
    def test_transfer_overdraw(self):
        with self.assertRaises(ValueError):a.parent_transfer(100,[('a',101)],100,accepted=True)
    def test_transfer_unaccepted(self):
        with self.assertRaises(ValueError):a.parent_transfer(100,[('a',10)],100,accepted=False)
    def transfer_fixture(self):
        p=accepted('Astar','electricity');p.update(IncludedInAstar=True)
        c=accepted('HistoricalEV','electricity',20);c.update(IncludedInAstar=True,Posting=False,Representation='EMBEDDED',OwnerAccount='Astar')
        return [p,c]
    def test_transfer_compiled_once(self):
        rows=self.transfer_fixture();out,proof=a.apply_astar_transfers(rows,'SG',2019,[rows[1]['RowID']],100)
        material=a.materialise(out,'SG',2019,{'SG:electricity':{'id':'SG0','country':'SG','carrier':'electricity'}})
        self.assertEqual([r['annual_mwh'] for r in material],[80,20]);self.assertEqual(rows[0]['ConvertedMWh'],100)
    def test_transfer_repeated_rejected(self):
        rows=self.transfer_fixture();out,proof=a.apply_astar_transfers(rows,'SG',2019,[rows[1]['RowID']],100)
        with self.assertRaises(ValueError):a.apply_astar_transfers(out,'SG',2019,[rows[1]['RowID']],80)
    def test_transfer_unaccepted_membership(self):
        rows=self.transfer_fixture();rows[1]['HumanAcceptance']='VALUE_ONLY'
        with self.assertRaises(ValueError):a.apply_astar_transfers(rows,'SG',2019,[rows[1]['RowID']],100)
    def test_transfer_flag_without_parent_debit_rejected(self):
        rows=self.transfer_fixture();rows[1].update(TransferredFromAstar=True,Posting=True,Representation='EXPLICIT',OwnerAccount='HistoricalEV')
        with self.assertRaises(ValueError):a.validate_ledger(rows)
    def test_transfer_parent_tamper_rejected(self):
        rows=self.transfer_fixture();out,_=a.apply_astar_transfers(rows,'SG',2019,[rows[1]['RowID']],100)
        out[0]['ConvertedMWh']=100
        with self.assertRaises(ValueError):a.validate_ledger(out)
    def test_road_final_energy(self):
        p=a.road_energy(100,.2,{'oil':.7,'gas':.2,'biomass':.1},basis='final_energy_MWh',accepted=True)
        self.assertEqual(p['EVFinalEnergy'],20);self.assertAlmostEqual(sum(p['ResidualFuel'].values()),80)
    def test_road_boundaries(self):
        for share in [0,1]:
            r=a.road_energy(100,share,{'oil':1},basis='final_energy_MWh',accepted=True)
            self.assertEqual(r['EVFinalEnergy']+sum(r['ResidualFuel'].values()),100)
    def test_road_dimensionless_vehicle_share_rejected(self):
        with self.assertRaises(ValueError):a.road_energy(100,.2,{'oil':1},basis='final_energy_MWh',accepted=True,share_kind='vehicles')
    def test_road_wrong_basis(self):
        with self.assertRaises(ValueError):a.road_energy(100,.2,{'oil':1},basis='kWh_per_km',accepted=True)
    def test_road_unaccepted(self):
        with self.assertRaises(ValueError):a.road_energy(100,.2,{'oil':1},basis='final_energy_MWh',accepted=False)
    def test_road_wrong_weights(self):
        with self.assertRaises(ValueError):a.road_energy(100,.2,{'oil':.9},basis='final_energy_MWh',accepted=True)
    def test_road_invalid_share(self):
        with self.assertRaises(ValueError):a.road_energy(100,1.2,{'oil':1},basis='final_energy_MWh',accepted=True)
    def test_future_no_fallback(self):
        with self.assertRaisesRegex(ValueError,'FUTURE_DIRECT'):a.electric_evolution(100,2019,2030)
    def test_future_conversion_exclusion_required(self):
        with self.assertRaises(ValueError):a.electric_evolution(100,2019,2030,factor=2,accepted=True)
    def test_explicit_accepted_evolution(self):
        self.assertEqual(a.electric_evolution(100,2019,2030,factor=2,accepted=True,excludes_future_conversion=True),200)
    def allocation(self,**overrides):
        d=dict(annual=8760,country='SG',nodes={'a':{'country':'SG','weight':.3},'b':{'country':'SG','weight':.7}},
               shapes={'t1':1,'t2':3},physical_weights={'t1':2190,'t2':6570},expected_hours=8760);d.update(overrides)
        return a.allocate(**d)
    def test_spatial_temporal_four_levels(self):
        p=self.allocation();self.assertAlmostEqual(sum(v['t1']*2190+v['t2']*6570 for v in p.values()),8760)
        self.assertAlmostEqual(p['a']['t1']*2190+p['a']['t2']*6570,2628)
    def test_spatial_wrong_country(self):
        with self.assertRaises(ValueError):self.allocation(nodes={'a':{'country':'MY','weight':1}})
    def test_spatial_bad_weights(self):
        for weight in [.9,0,-1,float('nan')]:
            with self.subTest(weight=weight),self.assertRaises(ValueError):self.allocation(nodes={'a':{'country':'SG','weight':weight}})
    def test_temporal_wrong_ids(self):
        with self.assertRaises(ValueError):self.allocation(shapes={'a':1})
    def test_temporal_zero_shape(self):
        with self.assertRaises(ValueError):self.allocation(shapes={'t1':0,'t2':0})
    def test_temporal_wrong_hours(self):
        with self.assertRaises(ValueError):self.allocation(expected_hours=48)
    def test_temporal_invalid_physical_weight(self):
        with self.assertRaises(ValueError):self.allocation(physical_weights={'t1':0,'t2':8760})
    def test_materialise_valid(self):
        r=accepted();out=a.materialise([r],'SG',2019,{'SG:oil':{'id':'SG oil','country':'SG','carrier':'oil'}})
        self.assertEqual(len(out),1);self.assertEqual(out[0]['annual_mwh'],100)
    def test_materialise_wrong_destination(self):
        with self.assertRaises(ValueError):a.materialise([accepted()],'SG',2019,{'SG:oil':{'id':'MY oil','country':'MY','carrier':'oil'}})
    def test_materialise_unknown_year(self):
        with self.assertRaises(ValueError):a.materialise([accepted()],'SG',2030,{})


class PinnedInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global build,csv_bytes
        from build_research_demand import build,csv_bytes
        cls.tables,cls.report=build(ROOT);cls.rows=cls.tables['RESEARCH_DEMAND_LEDGER.csv']['rows']
    def test_11_raw_astar_no_numeric_acceptance(self):
        r=[x for x in self.rows if x['ChildAccount']=='Astar' and x['Year']==2019]
        self.assertEqual(len(r),11);self.assertTrue(all(x['ConvertedMWh']>0 for x in r));self.assertFalse(any(x['NumericAccepted'] for x in self.rows))
    def test_all_real_country_years_blocked(self):self.assertEqual(self.report['guarded_country_years'],44)
    def test_no_real_electricity_transfers(self):self.assertFalse(any(x['TransferredFromAstar'] for x in self.rows))
    def test_buildings_44_thermal_embedded(self):
        r=[x for x in self.rows if x['Sector']=='Buildings' and x['Year']==2019 and x['ChildAccount'].endswith(('SpaceHeat','WaterHeat'))]
        self.assertEqual(len(r),44);self.assertTrue(all(x['Representation']=='EMBEDDED' and x['ConvertedMWh'] is None and not x['Posting'] for x in r))
    def test_rail_never_additional_load(self):
        self.assertTrue(all(not x['Posting'] for x in self.rows if x['ChildAccount'].startswith('Rail')))
    def test_bunkers_four_accounts(self):
        r=[x for x in self.rows if x['Group']=='bunker' and x['Year']==2019]
        self.assertEqual(len(r),44);self.assertEqual(len(set(x['ChildAccount'] for x in r)),4)
    def test_agriculture_fuels_preserved(self):
        source=load_sources(ROOT)['energy_cache']['records']
        for fuel in ['oil','biomass','coal']:
            expected=sum(float(x['agriculture '+fuel])*1e6 for x in source if x['agriculture '+fuel] not in ('',None))
            actual=sum(x['ConvertedMWh'] for x in self.rows if x['Sector']=='Agriculture' and x['Year']==2019 and x['Carrier']==fuel and x['ConvertedMWh'] is not None)
            self.assertAlmostEqual(actual,expected,places=5)
    def test_missing_tl_industry_fuels_not_zero(self):
        r=[x for x in self.rows if x['Country']=='TL' and x['Sector']=='Industry' and x['Year']==2019 and x['Posting']]
        self.assertTrue(r);self.assertTrue(all(x['ConvertedMWh'] is None for x in r))
    def test_cache_zero_not_certified_zero(self):
        r=[x for x in self.rows if x['ZeroEvidence']=='CACHE_ZERO_UNVERIFIED']
        self.assertTrue(r);self.assertTrue(all(x['ConvertedMWh'] is None for x in r))
    def test_no_future_values_invented(self):self.assertTrue(all(x['ConvertedMWh'] is None for x in self.rows if x['Year']>2019))
    def test_build_is_deterministic(self):
        again,_=build(ROOT)
        for name,t in self.tables.items():self.assertEqual(csv_bytes(t),csv_bytes(again[name]))
    def test_csv_roundtrip_missing_and_zero(self):
        import csv,io
        data=list(csv.DictReader(io.StringIO(csv_bytes(self.tables['RESEARCH_DEMAND_LEDGER.csv']).decode('utf-8-sig'))))
        for original,read in zip(self.rows,data):
            if original['ConvertedMWh'] is None:self.assertEqual(read['ConvertedMWh'],'')
            elif original['ConvertedMWh']==0:self.assertEqual(float(read['ConvertedMWh']),0)
    def test_capsule_tamper_rejected(self):
        import shutil
        with tempfile.TemporaryDirectory() as d:
            dst=Path(d)/'research_inputs/demand/sources';shutil.copytree(ROOT/'research_inputs/demand/sources',dst)
            with (dst/'electricity.json').open('a') as f:f.write(' ')
            with self.assertRaises(ValueError):load_sources(d)
    def test_industry_source_carrier_preservation(self):
        sources=load_sources(ROOT)['industry_cache']['records']
        for x in sources:
            if x['carrier'] in ('electricity','heat','hydrogen'):continue
            expected=math.fsum(float(v) for k,v in x.items() if k not in ('country','carrier'))
            found=[r for r in self.rows if r['Year']==2019 and r['Country']==x['country'] and r['Sector']=='Industry' and r['Carrier']==x['carrier']]
            self.assertEqual(len(found),1)
            if expected>0:self.assertAlmostEqual(found[0]['ConvertedMWh'],expected,places=5)
            else:self.assertIsNone(found[0]['ConvertedMWh'])
    def test_all_numeric_rows_source_conservation(self):
        matrix=self.tables['RESEARCH_DEMAND_CONSERVATION_MATRIX.csv']['rows']
        self.assertEqual(sum(r['ConvertedMWh'] is not None for r in self.rows),sum(r['SourceToSector']=='PASS_SOURCE_TO_LEDGER' for r in matrix))
    def test_config_entry_point(self):
        from check_research_demand import check
        self.assertEqual(check(ROOT)['config_contract'],'PASS')
    def test_config_enabling_legacy_target_rejected(self):
        import shutil
        from check_research_demand import check
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'configs/research';p.mkdir(parents=True)
            text=(ROOT/'configs/research/baseline.yaml').read_text().replace('aeo8_generation_target: false','aeo8_generation_target: true')
            (p/'baseline.yaml').write_text(text)
            with self.assertRaisesRegex(ValueError,'aeo8_generation_target'):check(d)


if __name__=='__main__':unittest.main(verbosity=2)
