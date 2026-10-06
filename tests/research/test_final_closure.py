import sys,json,unittest,copy
from pathlib import Path
from decimal import Decimal as D
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts_project'))
from final_closure_inputs import derive_blends,eligible_unreported,read,record_fingerprint,validate_final_registry,LOW,HIGH,OUTSIDE
from carbon_architecture import install_power_policy

class FinalClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=R/'research_inputs/assembly_v1';s=cls.f/'sources';cls.prior=read(s/'PRE_FINAL_REGISTRY.json');cls.base=read(s/'BASE_RECONSTRUCTION.json');cls.env=read(R/'research/04_model_assembly/gate4/evidence/uncertainty/BLEND_UNCERTAINTY_ENVELOPES.json');cls.records=read(cls.f/'registry.json')['records'];cls.evidence=read(s/'FINAL_UN_REPORTING_EVIDENCE.json')
    def test_accepted_records_scientifically_unchanged(self):
        current={r['InputID']:r for r in self.records}
        for r in self.prior['records']:
            if r['Year']==2050 and r['Kind']=='DEMAND' and r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED':self.assertEqual(record_fingerprint(r),record_fingerprint(current[r['InputID']]))
    def test_blend_endpoints_and_separate_heat(self):
        lo=derive_blends(self.prior,self.base,self.env,LOW);hi=derive_blends(self.prior,self.base,self.env,HIGH)
        for l,h,e in zip(lo['parameters'],hi['parameters'],self.env['records']):
            P,B=D(e['P']),D(e['B']);self.assertEqual(D(l['Z']),min(P,B));self.assertEqual(D(h['Z']),0)
            self.assertEqual(D(l['UniqueQuantity']),max(P,B));self.assertEqual(D(h['UniqueQuantity']),P+B)
            self.assertEqual(D(l['UniqueEnergyMWh']),D(e['LowerEnergyMWh']));self.assertEqual(D(h['UniqueEnergyMWh']),D(e['UpperEnergyMWh']))
            self.assertIsNone(l['SourceReportedZ'])
    def test_not_only_pair_other_commodities_preserved(self):
        lo=derive_blends(self.prior,self.base,self.env,LOW)
        ident='ID:2050:Buildings:ServicesFuel:biomass'
        self.assertGreater(D(lo['records'][ident]['BaseMWh']),D(next(e for e in self.env['records'] if e['Country']=='ID' and e['TransactionCode']=='1235')['B'])*D('10220'))
    def test_ph_road_gasoline_and_diesel_separate(self):
        z=derive_blends(self.prior,self.base,self.env,LOW)
        r=z['records']['PH:2050:Transport:RoadResidualFuel:oil'];self.assertEqual(len(r['UncertaintyIDs']),2)
        originals={x['AccountID']:x for x in self.base['accounts']};raw=D(originals[r['BaseAccountID']]['ValueMWh'])
        deductions=sum(D(e['Z'])*D(next(x['PetroleumNCVMWhPerKton'] for x in self.env['records'] if x['UncertaintyID']==e['UncertaintyID'])) for e in z['parameters'] if e['UncertaintyID'] in r['UncertaintyIDs'])
        self.assertEqual(D(r['BaseMWh']),raw-deductions)
    def test_ph_rail_constant_and_metadata(self):
        for r in self.records:
            if r['Country']=='PH' and r['Account']=='RailNonElectric' and r['Year']==2050:
                self.assertEqual(r['GrowthNumerator'],r['GrowthDenominator']);self.assertEqual(r['Value'],float(D(r['BaseValueMWh'])));self.assertEqual(r['CandidateUnit'],'MWh/year');self.assertNotIn('2.581',r['Transformation'])
    def test_bad_version_or_repeated_pair_rejected(self):
        e=copy.deepcopy(self.env);e['records'][0]['Proof']['VersionReconciled']=False
        with self.assertRaises(ValueError):derive_blends(self.prior,self.base,e,LOW)
        e=copy.deepcopy(self.env);e['records'].append(e['records'][0])
        with self.assertRaises(ValueError):derive_blends(self.prior,self.base,e,LOW)
    def test_coverage_null_not_zero(self):
        rows=[r for r in self.records if r.get('Classification')==OUTSIDE];self.assertTrue(rows)
        for r in rows:self.assertIsNone(r['RawValue']);self.assertIsNone(r['Value']);self.assertFalse(r['Posting']);self.assertFalse(r['RequiredPhysical'])
        bad=copy.deepcopy(self.records);next(r for r in bad if r.get('Classification')==OUTSIDE)['Value']=0
        with self.assertRaises(ValueError):validate_final_registry(self.f,bad)
    def test_coverage_not_global_or_future_ban(self):
        for country,carrier,account in [('VN','gas','ResidentialFuel'),('BN','gas','ResidentialFuel'),('KH','oil','DomesticShippingFuel'),('ID','oil','InternationalShippingBunker')]:
            self.assertIsNone(eligible_unreported(dict(Country=country,Carrier=carrier,Account=account,Year=2050,Kind='DEMAND'),self.evidence))
        r=dict(Country='KH',Carrier='gas',Account='ResidentialFuel',Year=2050,Kind='EXTERNAL_SUPPLY');self.assertIsNone(eligible_unreported(r,self.evidence))
    def test_missing_coverage_symbol_refuses(self):
        e=copy.deepcopy(self.evidence);e['Findings'][0]['SourceSymbols']='0'
        self.assertIsNone(eligible_unreported(dict(Country='KH',Carrier='gas',Account='ServicesFuel',Kind='DEMAND',Year=2050),e))
    def test_sensitivity_never_accepted_by_baseline(self):
        upper=read(self.f/'variants/blend_no_overlap_upper/registry.json')
        with self.assertRaises(ValueError):validate_final_registry(self.f,upper['records'])
    def test_policy_off_and_pending_on_rejected_without_model(self):
        class N:pass
        n=N();terms=[dict(policy_weight=None,PolicyAttributionQualified=False,accepted=False)]
        self.assertFalse(install_power_policy(n,terms,2050,enabled=False,scope_complete=False,expected_hours=8760)['constraint_created'])
        with self.assertRaisesRegex(ValueError,'POLICY_ATTRIBUTION_PENDING'):install_power_policy(n,terms,2050,enabled=True,scope_complete=True,expected_hours=8760)

if __name__=='__main__':unittest.main()
