"""Read-only model/source inspection plus a paper DAG dry-run (no solver)."""
from engineering_review import *
from datetime import datetime, timezone
import importlib.metadata as metadata
import pypsa

def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    repo=BASE/'paper_reference';ev=HERE/'evidence';ev.mkdir(exist_ok=True)
    sys.path.insert(0,str(BASE/'upstream_sc_baseline/scripts'))
    from _helpers import _deep_merge_dicts,migrate_config
    current={}
    for name in ['config.default.yaml','configs/plotting.default.yaml','configs/solving.default.yaml','configs/bundle_config.yaml','configs/powerplantmatching_config.yaml','configs/config.asean.yaml']:
        current=_deep_merge_dicts(current,yaml.safe_load((BASE/'upstream_sc_baseline'/name).read_text()))
    current=migrate_config(current)
    (ev/'UPSTREAM_EFFECTIVE_CONFIG.json').write_text(json.dumps(current,indent=2,default=str))
    cfg=json.loads((HERE.parent/'00_source_provenance/effective_config/baseline-aims-3H_2025.json').read_text())
    # YAML integer year keys recover types lost in JSON network metadata serialization.
    def yearkeys(x):
        if isinstance(x,dict):return {int(k) if isinstance(k,str) and len(k)==4 and k.isdigit() and 1900<=int(k)<=2200 else k:yearkeys(v) for k,v in x.items()}
        if isinstance(x,list):return [yearkeys(v) for v in x]
        return x
    cfg=yearkeys(cfg)
    (ev/'PAPER_EFFECTIVE_CONFIG.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
    target='results/baseline-aims-3H/postnetworks/elec_s_100_ec_lv2.0__3h_2025_0.071_DEC_0export.nc'
    cmd=[str(Path(sys.executable).parent/'snakemake'),'--cores','1','--dry-run','--configfile',str(ev/'PAPER_EFFECTIVE_CONFIG.yaml'),'--',target]
    start=datetime.now(timezone.utc).isoformat()
    try:
        p=subprocess.run(cmd,cwd=repo,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
        text=p.stdout;rc=p.returncode
    except subprocess.TimeoutExpired as ex:text=(ex.stdout or b'').decode() if isinstance(ex.stdout,bytes) else (ex.stdout or '');rc='TIMEOUT_90S'
    (ev/'PAPER_DRYRUN.log').write_text(text)
    result={'start_time':start,'end_time':datetime.now(timezone.utc).isoformat(),'command':cmd,'returncode':rc,
     'classification':'DAG_PREFLIGHT_ONLY_NOT_FORMAL_RUN','config_sha256':sha(ev/'PAPER_EFFECTIVE_CONFIG.yaml'),
     'installed_versions':{k:metadata.version(k) for k in ['pypsa','linopy','snakemake','pandas','numpy','scipy','xarray','atlite','highspy','gurobipy']},
     'full_year_cutout_present':(OLD/'cutouts/asean-2013-era5.nc').exists(),
     'available_cutouts':[{'file':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in (OLD/'cutouts').glob('*.nc')],
     'paper_env_sha256':sha(repo/'envs/environment.yaml'),
     'paper_lock_sha256':sha(repo/'envs/linux-64.lock.yaml')}
    (ev/'environment-freeze.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
    (ev/'paper-environment.yaml').write_bytes((repo/'envs/environment.yaml').read_bytes())
    try:
        import gurobipy as gp
        with gp.Env(empty=True) as e:
            e.setParam('OutputFlag',0);e.start()
            result['gurobi_license_initialization']='SUCCESS (does not prove model-size eligibility)'
    except Exception as ex:result['gurobi_license_initialization']=str(ex)
    (HERE/'PAPER_PREFLIGHT.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2));print(text[-3000:])
    # Targeted topology records: keep source identities, never invent endpoint.
    topo={}
    for version in ['0.1','0.1.1']:
        for kind in ['buses','transformers','lines']:
            path=OLD/f'data/osm-plus-prebuilt/{version}/all_{kind}_build_network.csv'
            if not path.exists():continue
            df=pd.read_csv(path,dtype=str,keep_default_na=False)
            sel=df.apply(lambda col:col.isin(['765','766','transf_524_0']),axis=0).any(axis=1)
            topo[str(path.relative_to(OLD))]={'sha256':sha(path),'columns':list(df),'rows':df[sel].to_dict('records')}
    for name in ['base','base_extended','elec','elec_s']:
        path=OLD/f'networks/baseline-aims-3H-tutorial/{name}.nc'
        if not path.exists():continue
        n=pypsa.Network(path)
        loads=n.loads[n.loads.bus.isin(['765','766'])]
        topo[name]={'sha256':sha(path),'buses':n.buses.reindex(['765','766']).to_dict('index'),
         'transformers':n.transformers[n.transformers.bus0.isin(['765','766'])|n.transformers.bus1.isin(['765','766'])].to_dict('index'),
         'generators':n.generators[n.generators.bus.isin(['765','766'])].to_dict('index'),
         'load_mean_MW':n.loads_t.p_set.reindex(columns=loads.index).mean().to_dict(),
         'dangling_transformers':n.transformers[~n.transformers.bus0.isin(n.buses.index)|~n.transformers.bus1.isin(n.buses.index)].to_dict('index'),
         'mean_total_load_MW':float(n.loads_t.p_set.sum(axis=1).mean()),'total_generator_MW':float(n.generators.p_nom.sum())}
    (HERE/'TOPOLOGY_TRACE.json').write_text(json.dumps(topo,indent=2,default=str))

if __name__=='__main__':main()
