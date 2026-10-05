"""Bounded residual audit using current selected contracts and cached source IDs.

No scientific parameters, source queries or production quantities are altered.
Candidate name/coordinate links are review evidence, never duplicate proof.
"""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,json,hashlib,re,unicodedata,math
from reconstruct_base_accounts import reconstruct,Reconstruction,commodity,norm,account_for_transaction,row_id
from residual_account_mapping import build_crosswalk,reconcile_commodity_scope

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def tokens(s):return set(re.findall(r'[a-z0-9]+',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()))-{'power','plant','station','hydroelectric','hydropower','thermal','project','the','unit'}
def distance(a,b):
    if any(v is None for v in [*a,*b]):return None
    la,lo,lb,lob=map(math.radians,[*a,*b]);v=math.sin((lb-la)/2)**2+math.cos(la)*math.cos(lb)*math.sin((lob-lo)/2)**2;return 6371*2*math.asin(min(1,math.sqrt(v)))

def audit(repo,output):
    a=repo/'results_project/assembly_v1/assets';s=repo/'research_inputs/assembly_v1/sources';g=repo/'research/04_model_assembly/gate4'
    stock=read(a/'SELECTED_ASSET_SURVIVAL_2050.json');u={r['AssetID']:r for r in stock['unit_evidence']['records']}
    data=read(repo/'research_inputs/assembly_v1/registry.json');base=reconstruct(s)
    cross=build_crosswalk(base,s,data,read(g/'UNSD_TARGETED_RETRIEVAL_RECEIPT.json'))
    requests=[]
    for r in cross:
        requests.append(dict(RequestID=r['RequestID'],Country=r['Country'],Year=r['Year'],CommodityCodeAndName=r['MemoCommodity']+' / SDMX'+r['MemoSDMXCode']+' / '+r['MemoName'],TransactionCodeAndName=r['Transaction']+' / '+r['OfficialTransaction'],CompatibleParentVersion=dict(rows=r['ParentRows'],files=r['ParentSourceFiles'],sha256=r['ParentSourceVersions'],quantities=r['ParentValues'],unit=r['RawUnit'],footnotes=r['ParentFootnotes']),ExactOfficialEntryOrQuery=r['ExactRequestURL'],OfficialEntry=r['OfficialEntry'],ExistingRetrievalResult=r['RequestStatus'],ExistingReceipt=dict(file=r['PriorReceiptFile'],sha256=r['PriorReceiptSHA256'],wildcard=r['PriorWildcardReceipt'],wildcard_status=r['PriorWildcardStatus']),RequiredFields=r['RequiredFields'],AffectedAccounts=r['AffectedTargetAccounts'],RequestMappingQualified=True,SourceOverlapResolved=False,NewQueryExecuted=False))
    save(output/'EXACT_SOURCE_REQUESTS.json',requests)
    b=Reconstruction(read(s/'UNSD_2019_SOURCE_CAPSULE.json'),read(s/'FROZEN_UPSTREAM_CONVERSIONS.json'));lpg=[]
    for country in ['MM','TL']:
        rows=[r for r in b.rows if r['Country']==country and commodity(r['Commodity'])=='liquefied petroleum gas (lpg)'];parent=next(r for r in rows if norm(r['Transaction'])=='final energy consumption');parts=[r for r in rows if account_for_transaction(r['Transaction']) is not None]
        control=reconcile_commodity_scope(parent,parts);alias=next(r for r in parts if r['Transaction']=='Consumption by other consumers not elsewhere specified')
        lpg.append(dict(Country=country,Year=2019,Commodity='LPG',Control=control,AllOriginalRows=rows,ExclusiveLeaves=[row_id(r) for r in parts],RecoveredNECRow=row_id(alias),RecoveredRawQuantity=alias['Quantity'],RecoveredMWh=str(b.convert(alias)[0]),OriginalFootnotes=alias['Quantity Footnotes'],Definition='UNdata LP trID1234 equals DSD1234; excludes Consumption by other subtotal123',QuantityMethod='ASSEMBLY_V1_OTHER_NEC_CONSTANT_2019',MechanicalSourceRecovery=True,NewScientificAssumption=False))
    save(output/'LPG_SOURCE_CLOSEOUT.json',lpg)
    ev=read(repo/'research_inputs/asset_survival/GPD_COHORT_SOURCE_REVIEW.json');gem=read(repo/ev['gem_identity_file']);gem_by={x['ID']:x for x in gem}
    records=ev['records'];close=[];known_duplicates=[]
    for r in records:
        raw=r['raw'];unit=u['GPD:'+raw['gppd_idnr']]
        if raw['commissioning_year'] is None:continue
        if raw['commissioning_year']+unit['Lifetime']<=2050:continue
        if r['IdentityStatus']=='DISJOINT_FROZEN_SOURCE_SELECTION':continue # already integrated cohort, preserved
        verdict=r.get('ResidualCloseoutStatus','INSUFFICIENT_IDENTITY_EVIDENCE')
        if r['IdentityStatus']=='DUPLICATE_EXISTING_GEM_SITE':verdict='CONFIRMED_DUPLICATE_REPRESENTED'
        candidates=[]
        for z in gem:
            gu=u.get('GEM:'+z['ID'])
            if not gu or gu['Country']!=unit['Country'] or gu['Technology']!=unit['Technology']:continue
            f=z['Fields'];names=[v for k,v in f.items() if 'name' in k.lower() and v and 'owner' not in k.lower()];owners=[v for k,v in f.items() if k.lower()=='owner' and v]
            match=max((len(tokens(raw['name'])&tokens(name))/max(1,len(tokens(raw['name'])|tokens(name))) for name in names),default=0.)
            owner=max((len(tokens(raw['owner'])&tokens(name))/max(1,len(tokens(raw['owner'])|tokens(name))) for name in owners),default=0.) if raw['owner'] else 0.
            dist=distance((raw['latitude'],raw['longitude']),(f.get('Latitude'),f.get('Longitude')))
            candidates.append(dict(GEMID=z['ID'],Names=names,Owners=owners,CapacityMW=gu['OriginalCapacity'],StartYear=gu['CommissioningYear'],Status=gu['AssetClass'],SourceStatus=f.get('Status'),NameTokenSimilarity=match,OwnerTokenSimilarity=owner,DistanceKm=dist,ExactCapacityMatch=math.isclose(gu['OriginalCapacity'],raw['capacity_mw']),EvidenceClass='CANDIDATE_RELATION_ONLY_NOT_DUPLICATE_PROOF',SourceFile=z['File'],SourceRow=z['Sheet']+':'+str(z['Line'])))
        candidates=sorted(candidates,key=lambda x:(-x['NameTokenSimilarity'],-x['OwnerTokenSimilarity'],x['DistanceKm'] if x['DistanceKm'] is not None else float('inf')))[:3]
        out=dict(AssetID=unit['AssetID'],Country=unit['Country'],Technology=unit['Technology'],PlantName=raw['name'],ConditionalSurvivingMW=raw['capacity_mw'],ReportedPlantYear=raw['commissioning_year'],Status=verdict,RelatedGEMIDs=r.get('RelatedGEMIDs',[]),Evidence=r['Evidence'],Source=raw['source'],SourceURL=raw['url'],OriginalCoordinates=[raw['latitude'],raw['longitude']],Owner=raw['owner'],CachedMatchingEvidence=r.get('NearestOriginalParents',[]),BatchIdentityCandidates=candidates,ActualAddedMW=0.,RemainingQualification='Separate resource contract still required for every independent GPD hydro; seven-pool GEM decision does not cover GPD' if unit['Technology']=='Hydro' else 'Correct conversion technology, status, identity, mapping and existing cost parameters required',ExistingSelection=unit['SurvivalStatus'],NewEvidence=r.get('ResidualEvidence',[]),AlreadyClosedBeforeThisRound=raw['gppd_idnr'] in ['WRI1023892','WRI1023890'])
        close.append(out)
    save(output/'GPD_SURVIVOR_IDENTITY_CLOSEOUT.json',close)
    # Cross-source missing-year review: preserve source-family totals separately.
    missing=[x for x in u.values() if x['SurvivalStatus']=='UNRESOLVED_COMMISSIONING'];missinggem={x['RawUnitID']:x for x in missing if x['AssetID'].startswith('GEM:')};edges=[]
    for r in records:
        if r['raw']['commissioning_year'] is not None:continue
        raw=r['raw'];possible=[]
        for ident,gu in missinggem.items():
            if gu['Country']!=r['Country'] or gu['Technology']!=r['Technology']:continue
            z=gem_by[ident];f=z['Fields'];names=[v for k,v in f.items() if 'name' in k.lower() and v and 'owner' not in k.lower()]
            shared=max((len(tokens(raw['name'])&tokens(name))/max(1,len(tokens(raw['name'])|tokens(name))) for name in names),default=0.)
            sameparent=gu['ParentAssetID']==r['ParentAssetID']
            if shared or sameparent:possible.append(dict(GEMID=ident,ParentRelation='SAME_FROZEN_PARENT' if sameparent else 'DIFFERENT_FROZEN_PARENT',GEMNames=names,GEMCapacityMW=gu['OriginalCapacity'],SharedNameScore=shared,DistanceKm=distance((raw['latitude'],raw['longitude']),(f.get('Latitude'),f.get('Longitude'))),Evidence='CANDIDATE_IDENTITY_RELATION_NOT_PROOF; no quantity sum or retirement inference'))
        edges.append(dict(GPDID=raw['gppd_idnr'],Country=r['Country'],Technology=r['Technology'],Name=raw['name'],CapacityMW=raw['capacity_mw'],Candidates=sorted(possible,key=lambda x:-x['SharedNameScore']),Status='REVIEW_CANDIDATE_LINKS' if possible else 'NO_STRONG_LINK_IN_CACHED_IDENTITY_FIELDS_NOT_PROOF_OF_INDEPENDENCE'))
    save(output/'MISSING_YEAR_CROSS_SOURCE_RELATIONS.json',edges)
    scopes=defaultdict(lambda:dict(Count=0,CapacityMW=0.,SourceIDs=[]))
    for z in missing:
        key=(z['AssetID'].split(':')[0],z['Country'],z['Technology']);v=scopes[key];v['Count']+=1;v['CapacityMW']+=z['OriginalCapacity'];v['SourceIDs'].append(z['AssetID'])
    save(output/'MISSING_YEAR_GROUPED_CHOICES.json',[dict(SourceFamily=k[0],Country=k[1],Technology=k[2],**v,NewYearEvidenceRecovered=False,PossibleChoice='Supply compatible source year or choose an explicitly uncertain stock scenario boundary; this audit accepts neither zero stock nor unlimited life',CurrentIntegratedMWChange=0,ApprovalStatus='PENDING',CrossFamilyAdditive=False) for k,v in sorted(scopes.items())])
    contract=read(a/'SELECTED_INTEGRATION_CONTRACT.json');pending=[r for r in contract['hydro_group_qualification']['groups'] if r['Status']=='PENDING'];old=read(g/'evidence/closure/HYDRO_CANDIDATES.json');hydro=[]
    for r in pending:
        pool=r['Country']+':'+r['Node'].rsplit(' ',1)[0]+':'+r['HydroSubtype'];candidates=[x for x in old if x['PoolID']==pool]
        hydro.append(dict(CurrentGroup=r,InputCandidates=candidates,CurrentSource='SELECTED_INTEGRATION_CONTRACT.json',CurrentContractSHA256=sha(a/'SELECTED_INTEGRATION_CONTRACT.json'),ProductionChanged=False,UniqueChoice='Choose one compatible unassigned source curve with its original energy/Emax envelope; alternatives not additive' if any(x.get('SourceAlreadyAllocated') is False for x in candidates) else 'Provide compatible2013 same-type group input and storage Emax if reservoir, or approve a separately sourced proxy',ApprovalStatus='PENDING'))
    save(output/'FIVE_HYDRO_CHOICES.json',hydro)
    summary=dict(memo_requests=len(requests),memo_new_queries=0,memo_source_overlap_resolved=0,lpg_raw_rows_recovered=len(lpg),lpg_recovered_mwh=sum(float(x['RecoveredMWh']) for x in lpg),gpd_review_records=len(close),gpd_review_mw=sum(r['ConditionalSurvivingMW'] for r in close),gpd_new_duplicate_mw=sum(r['ConditionalSurvivingMW'] for r in close if r['Status']=='CONFIRMED_DUPLICATE_REPRESENTED' and not r['AlreadyClosedBeforeThisRound']),gpd_status_mw={status:sum(r['ConditionalSurvivingMW'] for r in close if r['Status']==status) for status in sorted({r['Status'] for r in close})},gpd_actual_added_mw=0,gem_missing_year_mw=sum(r['OriginalCapacity'] for r in missing if r['AssetID'].startswith('GEM:')),gpd_missing_year_mw=sum(r['OriginalCapacity'] for r in missing if r['AssetID'].startswith('GPD:')),missing_year_candidate_links=sum(len(r['Candidates']) for r in edges),pending_hydro_groups=len(pending),pending_hydro_mw=sum(r['SurvivingCapacityMW'] for r in pending),solver_runs=0)
    save(output/'RESIDUAL_SOURCE_SUMMARY.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);audit(**vars(p.parse_args()))
