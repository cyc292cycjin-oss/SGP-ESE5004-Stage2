"""Validate evidence consistency and hashes; no modelling or scientific parameter changes."""
from pathlib import Path
import json,hashlib,re,datetime,subprocess
ROOT=Path(__file__).resolve().parent
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(x in p.relative_to(ROOT).parts for x in ['cache','__pycache__']))
def main():
    docs=['PAPER_CODE_PROVENANCE.md','SECTOR_COUPLING_PROVENANCE.md','INDUSTRIAL_DEMAND_TRACE.md','CARBON_VERSION_TRACE.md','DEA_COST_SOURCE_TRACE.md','RESULTS_PACKAGE_AUDIT.md','USER_INPUT_NEEDED_V2.md','SOURCE_PROVENANCE_STATUS.md']
    checks=[]
    def check(label,value):
        checks.append({'check':label,'passed':bool(value)})
    check('eight_requested_reports_exist',all((ROOT/n).stat().st_size>1000 for n in docs))
    failures=[]
    for name in docs:
        t=(ROOT/name).read_text(encoding='utf-8')
        for link in re.findall(r'\]\(([^)]+)\)',t):
            if '://' not in link and not (ROOT/link.split('#')[0]).exists():failures.append([name,link])
    check('relative_markdown_links_resolve',not failures)
    for log in ['FETCH_LOG.json','COST_FETCH_LOG.json','HISTORY_FETCH_LOG.json','AEO_FETCH_LOG.json']:
        records=read(log);records=records['items'] if isinstance(records,dict) else records
        check(log+'_successful_fetch_hashes',all(digest(ROOT/'official'/r['name'])==r['sha256'] for r in records if 'sha256' in r))
    s=read('RECOVERY_SUMMARY.json');check('archive_44_networks_and_15_directories',s['zip_file_count']==44 and s['zip_directories']==15)
    n=read('RESULTS_NETWORK_EVIDENCE.json')
    check('two_networks_report_author_run_sha',len(n)==2 and all(x['attrs']['meta_decoded']['git_commit'].startswith('5bacad702ccfed17ad19ab510fa710651e966f2c ') for x in n))
    check('weights_are_8760',all(set(x['snapshot_weightings'].values())=={8760.0} for x in n))
    check('baseline_has_no_CO2Limit','CO2Limit' not in n[0]['global_constraints']['global_constraints_i'])
    i=n[1]['global_constraints']['global_constraints_i'].index('CO2Limit')
    check('DEC_2050_saved_CO2Limit_is_100Mt',n[1]['global_constraints']['global_constraints_constant'][i]==1e8)
    check('author_industry_load_nonzero',all(x['loads_time_series']['industry electricity']['weighted_MWh']>0 for x in n))
    for r in read('RESULTS_MEMBER_HASHES.json'):
        p=ROOT/r['path'].replace('\\','/')
        check('member_hash_'+p.parent.name,digest(p)==r['sha256'] and p.stat().st_size==r['bytes'])
    d=read('INDUSTRY_DIAGNOSTIC.json')
    check('industrial_missingness_and_nonempty_national_source',all(d[str(y)]['final']['nan']==480 and d[str(y)]['base_asean']['nonzero_finite']==157 and d[str(y)]['all_rows_have_nan_in_dot_input'] for y in [2030,2040,2050]))
    check('GDP_TIFF_does_not_cover_ASEAN_longitude',d['gdp_raster']['bounds'][2]<90)
    check('global_GDP_source_has_nonzero_ASEAN_values',read('GDP_TIMOR_EVIDENCE.json')['raw_2015_asean_rectangle']['nonzero_finite']>0)
    check('three_current_precosts_equal_pinned_official_bytes',all(x['byte_equal'] for x in read('DEA_WORKBOOK_EVIDENCE.json')['cost_file_comparison']))
    check('AEO_author_tables_equal_current_input_bytes',len(s['AEO_author_current_comparison'])==3 and all(x['byte_equal'] for x in s['AEO_author_current_comparison']))
    result={'date':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'bad_links':failures,'passed':all(c['passed'] for c in checks),'scope':'read-only source/metadata consistency, no optimisation, no parameter confirmation'}
    (ROOT/'VALIDATION.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    hashes={p.relative_to(ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':digest(p)} for p in files() if p.name!='FILE_HASHES.json'}
    (ROOT/'FILE_HASHES.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'files_hashed':len(hashes),'bytes_hashed':sum(x['bytes'] for x in hashes.values()),'failures':[x for x in checks if not x['passed']]},indent=2))
    if not result['passed']:raise SystemExit(1)
if __name__=='__main__':main()
