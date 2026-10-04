"""Prepare review tables from existing evidence, without producing model inputs."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent
ROOT=R.parents[3]
D=R/'derived';D.mkdir(exist_ok=True)
OLD=R.parent.parent/'buildings_phase3a3'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
combined=read(R/'evidence/COMBINED_TESTS.json')
identity=read(R/'evidence/FINAL_INTEGRATION_IDENTITY.json')
key=lambda r:(r['fix'],r['case'],r['country'],r['sector'],r['metric'])
before={key(r):r for fix in ['E1','E2','E4'] for r in read(OLD/f'evidence/{fix}_before.json')['rows']}
matrix=[]
for row in combined['rows']:
    pre=before[key(row)]
    matrix.append(dict(fix=row['fix'],case=row['case'],country=row['country'],sector=row['sector'],
      metric=row['metric'],before=pre['actual'],expected=row['expected'],after=row['actual'],unit=row['unit'],
      absolute_error=row['absolute_error'],relative_error=row['relative_error'],tolerance=row['tolerance'],
      before_test_status=pre['test_status'],test_status=row['test_status'],
      evidence_type='SYNTHETIC_FUNCTION_REGRESSION',before_source='Phase3A3 frozen-U failure receipt (reused)',
      after_source='Phase3A4 independent Git integration branch',tested_commit=identity['tested_source_commit'],
      combined_commit=identity['combined_commit'],detail=row['detail']))

req=[]
def requirement(id,country,sector,fields,evidence,gap,kind,status,needed,blocking='YES'):
    req.append(dict(Requirement_ID=id,Country=country,Sector=sector,Required_Fields=fields,
       Existing_Evidence=evidence,Remaining_Gap=gap,Gap_Type=kind,Status=status,
       Human_Confirmation='PENDING',Needed_Action=needed,Blocks_E3=blocking,Final_Value=''))

requirements=[
 ('BASE','A source year; meter boundary; loss treatment; national target scope','Frozen demand-building code and UNSD2019 balances','No accepted bridge between network supply/load and final-meter electricity','BOUNDARY_AND_DATA','SCIENTIFIC_DECISION_REQUIRED','Decide final-meter/bus boundary and approve documented year/loss reconciliation'),
 ('ENDUSE','EndUse; EndUseShare; SourceYear; geographic scope','UNSD2019 aggregate fuel/electricity; Phase3A3 source candidates','No accepted complete country R/S space/water/cooking partition','DATA_AND_ACCEPTANCE','ASEAN_VALIDATION_PENDING','Approve source-specific end-use mapping; no uniform60/40'),
 ('DEVICE','DeviceType; DeviceInputShare; Efficiency_or_COP; PerformanceBasis','DEA/PyPSA source families and default conversion code traced','Historical input-energy device mix/performance not calibrated','DATA_AND_ACCEPTANCE','ASEAN_VALIDATION_PENDING','Provide or approve applicable historical device evidence; tag source class'),
 ('FUEL','Fuel; FinalEnergyUnit; HHV_LHV_Basis; calorific value; density/moisture','UNSD raw commodities and hard-coded conversion chain traced','Fuelwood volume conversion and fuel basis remain unresolved','DATA','ASEAN_VALIDATION_PENDING','Verify original unit and matching energy content; do not copy ambiguous factors'),
 ('COOKING','Cooking electricity/gas/LPG/biomass; exclusive destination','MalaysiaNEB2016 end-use table; Indonesia2019 sector conflict','Unpartitioned cooking must stay direct/fuel; not accepted heat share','DATA_AND_BOUNDARY','SCIENTIFIC_DECISION_REQUIRED','Choose explicit ledger destinations and approve fuel/end-use partition'),
 ('SPATIAL','Region; SpatialWeight; sector-specific mapping','Upstream population allocation; regional household samples','No accepted R/S heat-service geography or weights','BOUNDARY_AND_DATA','SCIENTIFIC_DECISION_REQUIRED','Approve country/region evidence and normalized cluster allocation'),
 ('TIME','TemporalSource; TimeZone; PhysicalSnapshotWeight; electric-input profile','BDEW benchmark; Hanoi water-use candidate; E2 guard','No accepted matched historical-electric and useful-service hourly shapes','DATA_AND_METHOD','ASEAN_VALIDATION_PENDING','Select water usage and real space-heating profile methods; validate pointwise residual'),
 ('FUTURE','BaseYear; TargetYear; direct-demand growth; useful-service evolution','Current future fuel-shift and population electricity scripts traced','Future gross electricity target meaning conflicts with endogenous conversion scope','BOUNDARY','SCIENTIFIC_DECISION_REQUIRED','Approve separate direct/service evolution; no new carbon policy'),
 ('DH','UsefulServiceBoundary; DH geography; network loss convention','Upstream potential.3/progress1/loss.15 recovered','Regional evidence and boundary not accepted','BOUNDARY_AND_DATA','REJECT_DEFAULT','Retain capability; do not adopt uniform ASEAN defaults'),
 ('STOCK','ExistingHeatingStock; geography; source year','European stock and missing ASEAN data traced','No verified ASEAN brownfield inventory','DATA_AND_BOUNDARY','REJECT_DEFAULT','Do not equate missing with zero; resolve later assembly scope'),
 ('ID_CONFLICT','2019 R sector definition; gasoline; LPG; electricity revisions','UNSD2019 and ESDMHEESI2019 recovered locally','Different household/private-transport coverage and values','DATA_AND_ACCEPTANCE','ASEAN_VALIDATION_PENDING','Jointly choose version/sector mapping; do not reclassify fuel automatically'),
 ('E3_IMPL','Accounting ownership; calibration order; selectors; input validation','E3 specification and integrated synthetic failure diagnostic','Numeric evidence gate not satisfied; generic rescaling remains','ENGINEERING_AFTER_DATA','ENGINEERING_FIX_REQUIRED','Only implement E3 after bridge and source gates pass; prohibit annual fillna for missing data'),
]
for id,fields,evidence,gap,kind,status,needed in requirements:
    requirement(id,'ID' if id=='ID_CONFLICT' else 'BN;KH;ID;LA;MY;MM;PH;SG;TH;TL;VN','Residential;Services',fields,evidence,gap,kind,status,needed,
                'FULL_SC_ASSEMBLY' if id in ['DH','STOCK'] else 'YES')
candidates={
 'BN':'UNSD2019 aggregate only in retained collection',
 'KH':'UNSD2019; ERIA pilot and BELDA selected household samples; KH balance report',
 'ID':'UNSD2019; ESDMHEESI2019 conflicting scope; ERIA pilot household sample',
 'LA':'UNSD2019; ERIA pilot household sample',
 'MY':'UNSD2019; NEB2016 Table42 R and Table47 commercial (older Peninsula survey basis); BELDA household sample',
 'MM':'UNSD2019 aggregate only in retained collection',
 'PH':'UNSD2019; ERIA pilot sample; HECS2011 metadata but local raw PDF unavailable',
 'SG':'UNSD2019; NEA typical-household end-use information, not matched R/S annual2019',
 'TH':'UNSD2019; ERIA/BELDA household samples; reported direct solar heat is not electric heating',
 'TL':'UNSD2019 aggregate; ASEAN10 sources exclude TL',
 'VN':'UNSD2019; selected household end-use studies; short Hanoi water-use experiment',
}
for c in ['BN','KH','ID','LA','MY','MM','PH','SG','TH','TL','VN']:
    for s in ['Residential','Services']:
        requirement(f'HIST_{c}_{s[0]}',c,s,'HistoricalElectricSpaceHeat; HistoricalElectricWaterHeat; Coverage; Year; NodeSnapshotMapping',
          candidates[c], 'No HUMAN-accepted matching-year/coverage historical electric-heating input and subtraction profile',
          'DATA_AND_ACCEPTANCE','ASEAN_VALIDATION_PENDING',
          'Review existing sources first; obtain only remaining end-use/device/time evidence needed for this account')

# Data dictionary: blank template supplied separately; never synthetic country rows.
schema=[]
def field(name,type,unit,required,definition,source,rule):
    schema.append(dict(Field=name,Type=type,Unit=unit,Required=required,Definition=definition,
       Evidence_Class=source,Missing_or_Validation_Rule=rule,Human_Confirmation='PENDING'))
fields=[
 ('Country','string','ISO2','YES','Country of the accounted service','Official balance','One of frozen11; never infer missing country'),
 ('Sector','enum','','YES','Residential or Services; separate accounts','Official sector definition','Do not silently map combined commercial/public rows'),
 ('Region','string','','CONDITIONAL','Subnational/climate source coverage','Survey/balance geography','National extrapolation needs acceptance'),
 ('Fuel','string','','YES','Raw carrier identity before mapping','Official balance','Preserve LPG and oil subclass when available'),
 ('FinalEnergy','number','See FinalEnergyUnit','YES','Observed final input energy at stated scope','Official balance/end-use survey','Blank is unknown; reported zero needs source'),
 ('FinalEnergyUnit','string','','YES','Original energy/mass/volume unit','Source table','Unresolved conversion stops'),
 ('FinalEnergyScope','enum','','YES','fuel_total; end_use; device_end_use','Source table','Prevents applying end-use/device share twice'),
 ('EnergyBasis','enum','','YES','Final input; not useful heat or primary energy','Source definition','Do not sum incompatible bases'),
 ('HHV_LHV_Basis','string','','CONDITIONAL','Fuel heat-value basis; electricity/NA explicitly labelled','Original fuel data','Match efficiency basis; no inferred HHV/LHV'),
 ('UnitConversion','string','','YES','Versioned raw unit to MWh_final expression','Physical units/source factors','Mass/volume requires sourced factor; no arbitrary value'),
 ('EndUse','enum','','YES','space_heating; water_heating; cooking; cooling; other; unclassified','Country/region evidence','Cooking/cooling never auto-map to H/I'),
 ('EndUseShare','number','fraction','CONDITIONAL','Fraction of declared fuel-total denominator','Country/region end-use evidence','Required for fuel_total; scope identity1 only for already isolated end use'),
 ('ShareDenominator','string','','YES','Exact sector/fuel/year/geography covered by share','Same source lineage','No mixing energy share and appliance penetration'),
 ('DeviceType','string','','THERMAL','Historical device for service reconstruction','National survey/literature','Missing device/mix blocks service calibration'),
 ('DeviceInputShare','number','fraction','THERMAL','Historical final-input-energy fraction within end use','Device energy/use evidence','Sum1; do not substitute stock-count share'),
 ('Efficiency_or_COP','number','MWh_useful/MWh_final','THERMAL','Historical conversion performance, not future optimized value','DEA/national survey/literature/PyPSA default/engineering assumption','Missing blocks; source class alone does not confer acceptance'),
 ('EfficiencySourceType','enum','','THERMAL','DEA; national_survey; literature; PyPSA_default; engineering_assumption','Exact source','Retain distinction; no automatic default adoption'),
 ('EfficiencySource','string','','THERMAL','File/version/table for efficiency or COP','Original performance source','Require device conditions and performance year'),
 ('PerformanceBasis','string','','THERMAL','Boundary/HHV-LHV/seasonal conditions for efficiency or COP','Performance source','Must match FinalEnergy basis and device aggregation'),
 ('UsefulService','number','MWh_th','DERIVED','Useful space/water energy only after reviewed conversion','Versioned transform','Blank until evidence gate; never copy FinalEnergy'),
 ('UsefulServiceBoundary','string','','THERMAL','Delivered useful service vs plant supply; losses separate','Human boundary decision','No default DH markup in service target'),
 ('HistoricalElectricHeating','number','MWh_el','ELECTRIC_THERMAL','Represented historical electricity to remove exactly once','Matched end-use input ledger','Not taken from future fuel-shift electricity_* fields'),
 ('AccountID','string','','YES','Unique account linked to A–M specification','Accounting ledger','Unique; prevent parent/child duplicate sum'),
 ('SourceRowID','string','','YES','Stable raw row or table-cell identity','Raw source','Track partitions/transfers to avoid double use'),
 ('RetainedDestination','string','','YES','Direct electric/fuel; useful service; unclassified','Accounting decision','Every energy amount retains a destination'),
 ('Source','string','','YES','Primary source name and exact version','Primary source','No anonymous reasonable default'),
 ('SourceURL','string','','YES','Source access link','Primary source','Retain migrated/archived URL history'),
 ('SourceFile','string','','YES','Local file reference','Local raw cache','File must exist; no external-only final input'),
 ('SourceSHA256','string','','YES','Hash of raw source file','Local bytes','Verify before export'),
 ('SourceLocation','string','','YES','Sheet/table/page/row','Raw source','Precise location required'),
 ('SourceYear','string','','YES','Measurement/reference year','Source metadata','Separate publication year'),
 ('PublicationVersion','string','','YES','Release/revision identity','Source metadata','Multiple reasonable versions need joint choice'),
 ('TargetYear','integer','year','YES','Model demand year','Accepted scenario','Year bridge explicit; no silent extrapolation'),
 ('YearBridge','string','','CONDITIONAL','Source-year to target-year transformation','Accepted method','Required when years differ'),
 ('SpatialAllocation','string','','YES','R/S-specific region→cluster mapping and weights','Geographic evidence','Finite nonnegative weights, per-country sum1'),
 ('TemporalSource','string','','YES','Profile source/method, R/S and space/water-specific','Measured/evidenced usage/climate','Water independent of HDD; BDEW reference only'),
 ('TimeZone','string','','YES','Local/UTC mapping and calendar','Time metadata','No implicit timezone shift'),
 ('PhysicalSnapshotWeight','string','hours','YES','Explicit physical-integration weights reference','Run calendar','Do not confuse with discounted objective weight'),
 ('Transformation','string','','YES','Versioned calculation and order','Research script/config','No hidden defaults'),
 ('Status','enum','','YES','SOURCE_RECOVERED; ACCEPT_STRUCTURE; ASEAN_VALIDATION_PENDING; ENGINEERING_FIX_REQUIRED; SCIENTIFIC_DECISION_REQUIRED; DATA_UPDATE_CANDIDATE; REJECT_DEFAULT; HUMAN_ACCEPTED','Evidence/decision record','Agent never sets HUMAN_ACCEPTED'),
 ('HumanConfirmationRecord','string','','YES_BEFORE_EXPORT','Date/person/decision ID for accepted source and value','Human decision','Pending blocks scientific export'),
]
for args in fields:field(*args)
for name,rows in [('COMBINED_MATRIX',matrix),('E3_REQUIREMENTS',req),('USEFUL_HEAT_SCHEMA',schema)]:
    (D/(name+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
(D/'INPUT_TEMPLATE_FIELDS.json').write_text(json.dumps([r['Field'] for r in schema],indent=2))
print(json.dumps(dict(matrix=len(matrix),requirements=len(req),schema_fields=len(schema),scientific_input_rows=0)))
