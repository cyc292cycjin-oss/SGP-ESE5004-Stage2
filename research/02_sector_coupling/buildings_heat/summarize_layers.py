from pathlib import Path
import ast,hashlib,json,subprocess
import pandas as pd
R=Path(__file__).resolve().parent; ROOT=R.parents[1]; E=R/'evidence'
def read(p):return json.loads(p.read_text())
configs={
 'frozen_upstream_merged':read(ROOT/'01_baseline_construction/evidence/UPSTREAM_EFFECTIVE_CONFIG.json'),
 'tutorial_network_metadata':read(ROOT/'00_model_audit/AUDIT_RUNTIME_EVIDENCE.json')['networks'][0]['meta'],
 'paper_network_metadata':read(ROOT/'00_source_provenance/effective_config/baseline-aims-3H_2025.json')}
def select(c):
    s=c.get('sector',{});return {k:c.get(k) for k in ['countries','snapshots','load_options','demand_data','build_shape_options','tutorial']}|{'enable_buildings':{k:s.get('enable',{}).get(k) for k in ['heat','residential','services']},'space_heat_share':s.get('space_heat_share'),'district_heating':s.get('district_heating'),'coal_shift':s.get('coal'),'tes':s.get('tes'),'boilers':s.get('boilers'),'chp':s.get('chp'),'micro_chp':s.get('micro_chp'),'solar_thermal_collector':s.get('solar_thermal_collector'),'only_elec_network':c.get('final_adjustment',{}).get('only_elec_network')}
out={k:select(c) for k,c in configs.items()}
out['note']='Merged upstream config is not a completed runtime effective config; tutorial and paper metadata come from already existing outputs.'
(E/'CONFIG_LAYERS.json').write_text(json.dumps(out,indent=2))
a=R/'source_snapshot/upstream/data/heat_load_profile_BDEW.csv';b=E/'eur_sec_0.7.0/data/heat_load_profile_BDEW.csv'
da=pd.read_csv(a,index_col=0);db=pd.read_csv(b,index_col=0)
same={'bytes_equal':a.read_bytes()==b.read_bytes(),'normalized_newlines_equal':a.read_text()==b.read_text(),'values_equal':da.equals(db),'max_numeric_difference':float((da-db).abs().max().max())}
(E/'BDEW_COMPARISON.json').write_text(json.dumps(same,indent=2))
G='/home/jin/research/SGP_ESE5004_Stage2/phase2/upstream_sc_baseline'
for label,args in {
 'SPLIT_ORIGINAL_COMMIT.txt':['show','--format=short','174ae272','--','config.default.yaml','scripts/build_base_energy_totals.py'],
 'COOLING_CODE_SEARCH.txt':['grep','-n','-i','-E','cooling|chiller|cold storage','a3616a68','--','scripts','config.default.yaml','configs/config.asean.yaml','Snakefile'],
}.items():
    p=subprocess.run(['git','-C',G,*args],capture_output=True);(R/'history'/label).write_bytes(p.stdout)
registry=pd.read_excel(R/'source_snapshot/upstream/data/demand/unsd/paths/Energy_Statistics_Database.xlsx')
(E/'UNSD_DOWNLOAD_REGISTRY.json').write_text(registry.to_json(orient='records',indent=2))
print(json.dumps({'BDEW':same,'config_layers':{k:{f:v.get(f) for f in ['enable_buildings','only_elec_network','load_options']} for k,v in out.items() if isinstance(v,dict)}},indent=2))
