from collect_sources import ROOT, git, save, fetch
import concurrent.futures,json

def main():
    api='https://api.github.com/repos/'
    sha='5bacad702ccfed17ad19ab510fa710651e966f2c'
    jobs=[('author_run_commit.json',api+'pypsa-meets-earth/pypsa-asean/commits/'+sha),('paper_pr25_commits.json',api+'pypsa-meets-earth/pypsa-asean/pulls/25/commits?per_page=100'),('earth_merge1086.json',api+'pypsa-meets-earth/pypsa-earth/pulls/1086'),('tech_manual_history.json',api+'PyPSA/technology-data/commits?sha=v0.13.2&path=inputs/manual_input.csv&per_page=15')]
    for p in ['configs/config.asean.yaml','configs/scenarios.asean.yaml','config.default.yaml','scripts/prepare_sector_network.py','scripts/prepare_network.py','scripts/final_asean_adjustment.py','scripts/solve_network.py','scripts/_helpers.py','Snakefile','envs/environment.yaml','data/AEO8-input/AEO8_Table_D15_Cost_Summary.csv','data/AEO8-input/AEO8_Table_D17_Declining_Factors.csv','data/AEO8-input/AEO8_Table_D18_Capital_Regional.csv']:
        jobs.append(('author_run/'+p,'https://raw.githubusercontent.com/pypsa-meets-earth/pypsa-asean/'+sha+'/'+p))
    jobs.append(('technology-data/inputs/Eurostat_inflation_rates.xlsx','https://raw.githubusercontent.com/PyPSA/technology-data/ec22a1843632fd28ecb9a139ee5156faf23324a3/inputs/Eurostat_inflation_rates.xlsx'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:result=list(pool.map(fetch,jobs))
    save('HISTORY_FETCH_LOG.json',json.dumps(result,indent=2));print([x for x in result if 'error' in x])
    for name,args in {
      'carbon_key_change':['show','5ea64e917e283064ff91a4cbb8a023305c9f8a71','--','scripts/prepare_sector_network.py','scripts/_helpers.py'],
      'asean_key_change':['show','c1d99d0617e027ebe01fa2dd1ce1f7160eaddd6e','--','configs/config.asean.yaml'],
      'carbon_introduction':['show','f6236a385c700d4023225b6a2946f0525ad76f68','--','scripts/prepare_sector_network.py'],
      'sector_merge_summary':['show','--format=short','--stat','a8987468ceda152ed1152f6c7bfa2ffb79da0837'],
      'gdp_history':['log','--all','--format=%H %ad %s','--date=short','-G','GDP|gdp','--','scripts/build_shapes.py','configs/bundle_config.yaml'],
      'sector_module_history':['log','--all','--format=%H %ad %s','--date=short','--','scripts/build_industrial_distribution_key.py'],
      'paper_notebooks':['ls-tree','-r','--name-only','99159edb','notebooks'],
    }.items():save('history/'+name+'.txt',git(*args))
if __name__=='__main__':main()
