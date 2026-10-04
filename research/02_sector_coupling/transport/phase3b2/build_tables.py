"""Build review-table JSON from explicit decisions and retained test evidence.

No model input is authored. Final CSVs are exported by artifact-tool.
"""
from pathlib import Path
import csv, hashlib, json, shutil, subprocess
R=Path(__file__).resolve().parent
B=R.parent/'phase3b1'
ROOT=R.parents[3]
D=R/'data';D.mkdir(exist_ok=True)
def write(name, data): (D/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
cols=['Mode','DemandRepresentation','EnergyCarrier','ElectricityTreatment','FuelTreatment','TemporalTreatment','SpatialTreatment','CarbonTreatment','FullSCStatus','Blocker','Reason']
rows=[
['Road EV','EXPLICIT fixed exogenous final-energy obligation','electricity at final-user charging input','A* historic transfer once; future direct parent excludes same service','No extra fuel / H2 for same EV obligation','Simple nonnegative normalized external charging shape; no DSM/V2G','Country to accepted existing-node weights','Generation stays in PolicyCO2_Power; same event once in reporting','REPRESENTATION_FROZEN; INPUT_IMPLEMENTATION_PENDING','G1; G2','R and EV energy share jointly defined; old adoption share not automatically reused'],
['Road residual fuel','FIXED / ACCOUNTED carrier-resolved aggregate','oil / gas / biomass / other accepted fuel','No precomputed fuel-conversion electricity in A*','Sum F_k = (1-sE)R; preserve actual fuel identity','Simple weighted annual obligation','Transparent existing country nodes','Direct combustion reporting; actual fuel/carbon origin; Power generation unchanged','REPRESENTATION_FROZEN; INPUT_IMPLEMENTATION_PENDING','G1; G2; G3','Positive cached gas/bio cannot silently become fossil liquid'],
['Rail electricity','EMBEDDED once in A* direct account','electricity','Keep within parent; no independent duplicate rail Load','Not applicable','Parent electricity profile','Parent allocation','Generation remains Power policy and full reporting once','REPRESENTATION_FROZEN; CONTAINMENT_PENDING','G1; G2','Must prove containment before suppressing standalone rail Load'],
['Rail fuel','EMBEDDED once in direct-fuel parent','diesel / biodiesel / other accepted rail fuel','Not part of road-only R','Retain fuel obligation once with rail subaccount tag','Parent fuel allocation','Parent allocation','Direct-fuel reporting includes rail combustion and recycled-carbon return','REPRESENTATION_FROZEN; CONTAINMENT_PENDING','G1; G2; G3','No separate rail Load; no lost fuel or CO2 when embedded'],
['Domestic shipping','FIXED DomesticShippingFuel','accepted shipping fuel; aggregate oil supply where justified','FT/electrolysis electricity endogenous, not preloaded','Mutually exclusive with same domestic direct-fuel amount','Annual fuel with simple normalized profile','Ports/coastal where supported; validated country weights','Domestic combustion reporting, not automatic Power cap extension','REPRESENTATION_FROZEN; SOURCE_AND_ASSEMBLY_PENDING','G1; G2; G3','by/in raw transaction omission and missing values preserved'],
['International shipping','FIXED separate InternationalShippingBunkerFuel','accepted bunker fuel','Conversion electricity endogenous','Separate bunker account; not ordinary domestic final energy','Annual fuel with simple normalized profile','Same transparent port mapping; keep reporting-country identity','International bunker reporting separately','REPRESENTATION_FROZEN; SOURCE_AND_ASSEMBLY_PENDING','G1; G2; G3','No inferred route/flag allocation or invented country zeros'],
['Domestic aviation','FIXED DomesticAviationFuel','kerosene / declared accepted fuel coverage','Conversion electricity endogenous','Remove duplicate domestic parent obligation only with evidence','Annual fuel with simple normalized profile','Existing airports or accepted transparent country allocation','Domestic direct combustion reporting','REPRESENTATION_FROZEN; SOURCE_AND_ASSEMBLY_PENDING','G1; G2; G3','Kerosene subtotal is not all possible aviation fuel'],
['International aviation','FIXED separate InternationalAviationBunker','kerosene / declared accepted bunker coverage','Conversion electricity endogenous','Separate bunker obligation; no domestic final-energy relabel','Annual fuel with simple normalized profile','Existing airports or accepted transparent country allocation','Separate international aviation combustion reporting','REPRESENTATION_FROZEN; SOURCE_AND_ASSEMBLY_PENDING','G1; G2; G3','No aircraft or route competition'],
['Synthetic fuel production','EXPLICIT existing FT supply option','H2 + stored CO2 + AC to aggregate oil','FT direct electricity and H2 production withdrawals endogenous','Meet existing fixed oil demand; no duplicate same-service H2 Load','Endogenous conversion and existing storage constraints','Existing legal supply/network locations','Power supply emissions retained; physical carbon origin/capture/re-emission traced','SUPPLY_OPTION_FROZEN; CHAIN_VALIDATION_PENDING','G2; G3','Existing component does not prove CO2/heat supply is reachable'],
['Road FCEV','DEFERRED','H2','No first-baseline same-service load','No new FCEV demand','Not applicable','Not applicable','Not applicable','DEFERRED_BY_USER','NONE','No further transport study required'],
['EV DSM / V2G','DEFERRED','electricity flexibility','No EV Store or reverse V2G Link in assembled baseline','Not applicable','Fixed EV shape; no optimized charging shift','Not applicable','Power generation accounted normally','DEFERRED_BY_USER; ASSEMBLY_MASK_CHECK','G2','Upstream switches exist; old charger limits are not accepted new constraints'],
['Direct shipping H2','DEFERRED','H2','Do not create fixed H2 demand for same oil service','Fixed shipping fuel remains','Not applicable','Not applicable','No new direct marine H2 scenario','DEFERRED_BY_USER','NONE','FT H2 input remains legitimate supply-chain flow'],
['Marine ammonia / methanol','DEFERRED','NH3 / methanol','No new marine conversion load','No new terminal marine fuel','Not applicable','Not applicable','Not applicable','DEFERRED_BY_USER','NONE','Industrial ammonia capability does not imply marine propulsion']]
boundary=[]
for r in rows:
    assert len(r)==len(cols)
    d=dict(zip(cols,r));d.update(DecisionAuthority='USER_PHASE3B2_REQUEST',NumericInputStatus='UNVERIFIED / PENDING; no numeric adoption',Evidence='TRANSPORT_MINIMUM_DEFENSIBLE_BASELINE.md; mode accounting documents')
    boundary.append(d)
write('TRANSPORT_FIRST_FULLSC_BOUNDARY',boundary)

before=json.loads((R/'evidence/SHIPPING_TEST_BEFORE.json').read_text(encoding='utf8'))
after=json.loads((R/'evidence/SHIPPING_TARGET_GUARD_AFTER.json').read_text(encoding='utf8'))
guard_before=json.loads((R/'evidence/SHIPPING_TARGET_GUARD_BEFORE.json').read_text(encoding='utf8'))
old={r['test']:r['status'] for r in before['tests']}
guard_old={r['test']:r['status'] for r in guard_before['tests']}
tests=[]
for i,r in enumerate(after['tests'],1):
    tests.append(dict(TestID=f'SHIP-{i:02}',Test=r['test'],Before=old.get(r['test'],guard_old[r['test']]),After=r['status'],EvidenceClass='VERIFIED_OFFLINE_REGRESSION',BeforeSource=('U a3616a68' if r['test'] in old else 'Stage1 512c6cc2'),Scope='Actual add_shipping function; recorder network; explicit GIS fixture; no solver',InputStatus='TEST_FIXTURE_NOT_MODEL_INPUT',CandidateCommit='85a32dc231458fd753445df38d422b78435b8aad',Evidence='evidence/SHIPPING_TEST_BEFORE.json; evidence/SHIPPING_TARGET_GUARD_BEFORE.json; evidence/SHIPPING_TARGET_GUARD_AFTER.json',NotProven='Full 11-country source acceptance / GIS / PyPSA integration / solve'))
write('TRANSPORT_FIX_TEST_MATRIX',tests)

prior=list(csv.DictReader((B/'TRANSPORT_MATERIALITY_REGISTER.csv').open(encoding='utf-8-sig',newline='')))
disposition={
'T01':('G1; G2','EXACTLY_ONCE_CONTRACT_FROZEN; NUMERICAL_PENDING','Actual EV and rail parent containment remains pending; no empty-subset zero shortcut'),
'T02':('G1; G2','REPLACEMENT_SPEC_CLOSED; IMPLEMENTATION_PENDING','Use target-year final energy + energy share; old production road chain unchanged'),
'T03':('G1; G2','RAIL_EMBEDDED_DECISION_CLOSED; CONTAINMENT_PENDING','Retain rail fuel in non-road parent; disable duplicate only after transfer'),
'T04':('G1','ACCEPTED_INPUT_GATE','Inherited DEFAULT forecasts and missing-to-zero do not become accepted inputs'),
'T05':('G2','ISOLATED_CANDIDATE_PASS; REAL_ASSEMBLY_PENDING','17 offline tests pass including actual Load target guards; neither real saved network nor source quantities repaired'),
'T06':('NONE','BOUNDARY_DECISION_CLOSED','Domestic and international separately fixed; report-country identity retained; numeric acceptance tracked G1'),
'T07':('G3','CONTRACT_FROZEN; SCOPE_IMPLEMENTATION_BLOCKED','Shared atmosphere must not expand original Power cap; no carbon patch this phase'),
'T08':('G3','REPORTING_CONTRACT_CLOSED; IMPLEMENTATION_PENDING','Rail direct-fuel reporting and separated bunker combustion must close carbon return'),
'T09':('NONE','DEFERRED_BY_USER; NOT_A_RESEARCH_BLOCKER','No DSM/V2G first baseline; component-mask correctness remains routine G2'),
'T10':('G2; G3','SUPPLY_DEMAND_CONTRACT_FROZEN','Existing FT/H2 supply normal; duplicate same-service fixed electricity/H2 prohibited'),
'T11':('G2','SIMPLE_ALLOCATION_ACCEPTED_IN_PRINCIPLE; CONSERVATION_PENDING','Country weights, physical time weights and true nodal totals still need actual assembly'),
'T12':('NONE','LIMITATION_CLOSED','No vehicle, charger, vessel, aircraft or behavior detail as prerequisite'),
'T13':('NONE','LIMITATION_CLOSED','External electrification energy scenario; no fleet purchase optimization; first baseline avoids hidden stock cap'),
'T14':('OUTSIDE_TRANSPORT_CLOSEOUT','HANDED_TO_FULL_MODEL_EXPERIMENT_DESIGN','Same accepted obligations across comparisons; regional carrier/trade boundary is model-level future choice'),
'T15':('G1','INPUT_ACCEPTANCE_GATE','Source raw/unit/year/heat-value chain and human confirmation required; no automatic update')}
material=[]
for row in prior:
    gate,status,reason=disposition[row['ItemID']]
    material.append(dict(ItemID=row['ItemID'],Item=row['Item'],CloseoutStatus=status,RemainingSystemGate=gate,DispositionReason=reason,CredibleSystemImpact=row['CredibleSystemImpactPath'],QuantifiedImpact='NOT_ESTIMATED_NO_SOLVE',DecisionAuthority='User Phase3B2 representation decisions; source review for findings',Evidence='TRANSPORT_PHASE3_CLOSEOUT.md; relevant mode accounting',FurtherTransportDeepDive='NO'))
material.append(dict(ItemID='T16',Item='Domestic navigation by/in raw transaction omission',CloseoutStatus='RAW_EVIDENCE_LOCATED; INPUT_RECONCILIATION_PENDING',RemainingSystemGate='G1',DispositionReason='Four retained diesel rows in KH/ID/PH/SG excluded by frozen exact-by filter; no raw/model data changed',CredibleSystemImpact='Lost domestic fuel changes supply, FT/H2 and country demand burden',QuantifiedImpact='POSITIVE_RAW_QUANTITIES_OBSERVED; SYSTEM_IMPACT_NOT_ESTIMATED',DecisionAuthority='Direct raw/code observation, not accepted corrected totals',Evidence='evidence/ACCOUNT_SOURCE_REVIEW.md; evidence/COUNTRY_ACCOUNT_OBSERVATIONS.json',FurtherTransportDeepDive='NO'))
write('TRANSPORT_MATERIALITY_CLOSEOUT',material)

request=Path(r'C:/Users/20122/.codex/attachments/ee08da1b-5b69-4872-a466-e9a9b5c6862c/已粘贴的文本.txt')
if request.exists(): shutil.copyfile(request,R/'evidence/USER_PHASE3B2_REQUEST.txt')
dependencies=[]
tracked=subprocess.check_output(['git','-C',str(ROOT),'ls-files','--',B.relative_to(ROOT).as_posix()]).decode().splitlines()
for name in tracked:
    p=ROOT/name
    # Read only tracked artifacts in the relevant prior audit, never junctions.
    if p.suffix not in ('.json','.md','.csv','.py','.yaml','.yml','.tex','.txt','.xlsx') and p.name!='Snakefile': continue
    dependencies.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
(R/'evidence/DEPENDENCY_MANIFEST.json').write_text(json.dumps(dict(prior_phase='3B1',prior_root_commit='390dcad8c654b70ec259a1eb0e45569e5d319478',reuse_only=True,dependencies=dependencies),indent=2),encoding='utf8')
print(json.dumps(dict(boundary_rows=len(boundary),tests=len(tests),materiality_rows=len(material),numeric_input_adoptions=0)))
