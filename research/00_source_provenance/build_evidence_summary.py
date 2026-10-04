"""Make compact deterministic indexes for the audit report; no model execution."""
from collect_sources import ROOT, REPO, git, save
import hashlib,json,collections,pandas as pd
def main():
    nets=json.loads((ROOT/'RESULTS_NETWORK_EVIDENCE.json').read_text())
    summaries=[]
    for n in nets:
        m=n['attrs']['meta_decoded'];scenario=m['run']['name'];year=m['wildcards']['planning_horizons']
        save(f'effective_config/{scenario}_{year}.json',json.dumps(m,indent=2,ensure_ascii=False))
        summaries.append({'scenario':scenario,'year':year,'git_commit':m['git_commit'],'pypsa':n['attrs']['network_pypsa_version'],'objective':n['attrs']['network_objective'],'objective_constant':n['attrs']['network_objective_constant'],'weights':n['snapshot_weightings'],'loads':n['loads_time_series'],'co2_budget':m['co2_budget'],'constraints':n['global_constraints'],'sha256':n['sha256']})
    entries=json.loads((ROOT/'RESULTS_ZIP_DIRECTORY.json').read_text())['entries']
    files=[e for e in entries if not e['name'].endswith('/')]
    summary={'networks':summaries,'zip_entries':len(entries),'zip_file_count':len(files),'zip_directories':len(entries)-len(files),'scenario_counts':dict(collections.Counter(e['name'].split('/')[1] for e in files))}
    aeo=[]
    for p in (ROOT/'official/author_run/data/AEO8-input').glob('*.csv'):
        cur=ROOT.parent/'00_model_audit/input_snapshot/data/AEO8-input'/p.name
        aeo.append({'file':p.name,'comparison_path':str(cur),'author_sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),'current_sha256':hashlib.file_digest(cur.open('rb'),'sha256').hexdigest(),'byte_equal':p.read_bytes()==cur.read_bytes(),'dataframe_equal':pd.read_csv(p).equals(pd.read_csv(cur))})
    summary['AEO_author_current_comparison']=aeo
    for fn in ['build_shapes.py','build_population_layouts.py','build_clustered_population_layouts.py','build_industrial_distribution_key.py','build_base_industry_totals.py','build_industry_demand.py','append_cost_data.py','process_cost_data.py']:
        save('current_source/'+fn,git('show','ce327bfa:scripts/'+fn))
    save('history/original_sector_header.txt',git('show','42f4a1b3110a35dc7b82614ac28dbdb93d155b01:scripts/prepare_sector_network.py'))
    save('history/sector_merge_commit.txt',git('show','-s','--format=%H%n%ad%n%s%n%P','--date=iso-strict','a8987468ceda152ed1152f6c7bfa2ffb79da0837'))
    # Verify two key currency conversions from the frozen inflation table.
    t=pd.read_excel(ROOT/'official/technology-data/inputs/Eurostat_inflation_rates.xlsx',sheet_name='Sheet 1',index_col=0,header=8)
    row=t.loc['European Union - 27 countries (from 2020)'];factors={}
    for start in [2010,2015]:
        values={year:float(row[str(year)]) for year in range(start+1,2021)}
        product=1.
        for rate in values.values():product*=1+rate/100
        factors[str(start)]={'rates_percent':values,'factor_to_2020':product}
    summary['inflation']=factors
    summary['fuel_arithmetic']={'gas_21_6_EUR2010_to_EUR2020':21.6*factors['2010']['factor_to_2020'],'coal_8_4_EUR2010_to_EUR2020':8.4*factors['2010']['factor_to_2020'],'fuelcell_1100_EUR2015_to_EUR2020':1100*factors['2015']['factor_to_2020']}
    save('RECOVERY_SUMMARY.json',json.dumps(summary,indent=2,ensure_ascii=False));print(json.dumps(summary,indent=2,ensure_ascii=False)[:2500])
if __name__=='__main__':main()
