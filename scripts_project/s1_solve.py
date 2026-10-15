"""S1 solve driver: LP build, one solve, raw primal/dual export, V5 group A + B1/B11/B12 gates.

Local use (S1 supplement 02): SMOKE_TEST_ONLY on a truncated horizon with HiGHS; nothing it
produces may enter a result table. Cloud use (supplement 01, paused): the 365x24h network with
Gurobi Barrier+Crossover and the D-5 parameter set. One optimize call per invocation; never retried.

    python scripts_project/s1_solve.py --network <nc> --scenario integrated --output <dir> \
        --solver highs --truncate 56 --label SMOKE_TEST_ONLY --authorization "S1_SUPPLEMENT_02 §1.3"
"""
from pathlib import Path
import argparse,hashlib,json,os,sys,threading,time,traceback,platform
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))

D5_GUROBI={'Method':2,'Crossover':-1,'BarConvTol':1e-9,'Aggregate':1,'AggFill':0,'PreDual':0,'Seed':123,'Threads':4,'SoftMemLimit':65.,'LogToConsole':0,'OutputFlag':1}
D5_SOURCE='research/05_baseline_evolution/20261011/d_stage/release_d5/C06_EFFECTIVE_MODEL_PARAMETERS.json (non-default set) + D-5 overrides Crossover=-1, TimeLimit'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    def conv(o):
        if isinstance(o,np.generic):return o.item()
        if isinstance(o,(pd.Timestamp,)):return str(o)
        raise TypeError(type(o).__name__)
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False,default=conv)+'\n')

class Sampler(threading.Thread):
    def __init__(self,path,interval=1.):
        super().__init__(daemon=True);self.path=Path(path);self.interval=interval;self.peak=0;self.stop=threading.Event()
        import psutil;self.proc=psutil.Process()
    def run(self):
        with self.path.open('a') as f:
            while not self.stop.wait(self.interval):
                rss=self.proc.memory_info().rss
                for ch in self.proc.children(recursive=True):
                    try:rss+=ch.memory_info().rss
                    except Exception:pass
                self.peak=max(self.peak,rss);f.write(json.dumps(dict(epoch=time.time(),rss=rss,peak=self.peak))+'\n');f.flush()

def objective_constant(m):
    for getter in (lambda:m.objective.const,lambda:m.objective.expression.const):
        try:
            v=getter();v=float(np.asarray(v).reshape(-1)[0]) if np.ndim(v) else float(v)
            return 0. if np.isnan(v) else v
        except Exception:continue
    return 0.

def export_lp(m,lp_dir):
    """CSC export of the linopy model in original units (D=R=1) for the V4/V5 KKT algebra."""
    lp_dir=Path(lp_dir);lp_dir.mkdir(parents=True,exist_ok=True);M=m.matrices
    A=M.A.tocsc();c=np.asarray(M.c,dtype='<f8');lb=np.asarray(M.lb,dtype='<f8');ub=np.asarray(M.ub,dtype='<f8')
    sense=np.asarray(M.sense);b=np.asarray(M.b,dtype='<f8')
    # linopy MatrixAccessor.sense is dtype <U1: '=', '<' (<=), '>' (>=)
    if not set(np.unique(sense))<= {'=','<','>'}:raise ValueError('Unexpected constraint sense symbols: '+str(np.unique(sense)))
    row_lower=np.where(np.isin(sense,['=','>']),b,-np.inf).astype('<f8');row_upper=np.where(np.isin(sense,['=','<']),b,np.inf).astype('<f8')
    arrays=dict(cost=c,col_lower=lb,col_upper=ub,row_lower=row_lower,row_upper=row_upper,start=A.indptr.astype(np.int64),index=A.indices.astype(np.int64),value=A.data.astype('<f8'),vlabels=np.asarray(M.vlabels,dtype=np.int64),clabels=np.asarray(M.clabels,dtype=np.int64))
    meta=dict(num_col=int(A.shape[1]),num_row=int(A.shape[0]),nnz=int(A.nnz),sense=1,offset=objective_constant(m),units='ORIGINAL_UNSCALED',arrays={})
    for k,v in arrays.items():
        p=lp_dir/(k+'.npy');np.save(p,v);meta['arrays'][k]=dict(file=k+'.npy',count=int(len(v)),dtype=v.dtype.str,sha256=sha(p))
    meta['row_senses']={{'=':'=','<':'<=','>':'>='}[s]:int((sense==s).sum()) for s in ['=','<','>']}
    save(lp_dir/'MATH_PROBLEM.json',meta);return meta,M

def reduced_costs(m,solver):
    """Solver-native reduced costs keyed by linopy variable label."""
    sm=m.solver_model
    if solver=='gurobi':
        names=[v.VarName for v in sm.getVars()];rc=sm.getAttr('RC',sm.getVars());return {int(k[1:]):float(v) for k,v in zip(names,rc) if k.startswith('x')}
    if solver=='highs' and sm is not None:
        lp=sm.getLp();names=list(lp.col_names_);sol=sm.getSolution();rc=list(sol.col_dual)
        if len(names)!=len(rc):raise ValueError('HiGHS column names/reduced costs misaligned')
        return {int(k[1:]):float(v) for k,v in zip(names,rc) if k.startswith('x')}
    raise ValueError('Solver model not retained; native reduced costs unavailable')

def structural_supply_diagnosis(n):
    """Infeasibility localisation without changing the model: per-country zero-emission supply
    potential (renewable p_nom_max x availability, hydro, nuclear allowed?) against electricity demand."""
    w=n.snapshot_weightings.generators;out={}
    pmax=n.get_switchable_as_dense('Generator','p_max_pu')
    for c in sorted(set(n.buses.country.dropna())-{''}):
        buses=set(n.buses.index[n.buses.country==c]);g=n.generators[n.generators.bus.isin(buses)]
        demand=float((n.loads_t.p_set[[l for l in n.loads.index if n.loads.at[l,'bus'] in buses]].sum(axis=1)*w).sum())
        ren=g[(g.carrier.isin(['solar','solar rooftop','onwind','offwind-ac','offwind-dc']))&g.p_nom_extendable]
        potential=float(sum((pmax[k]*w).sum()*min(float(z.p_nom_max),1e9) for k,z in ren.iterrows()))
        hydro_gen=g[g.carrier.isin(['ror existing'])];hydro_e=float(sum((pmax[k]*w).sum()*float(z.p_nom) for k,z in hydro_gen.iterrows()))
        su=n.storage_units[n.storage_units.bus.isin(buses)&n.storage_units.carrier.isin(['hydro existing'])]
        inflow=n.get_switchable_as_dense('StorageUnit','inflow');hydro_inflow=float(sum((inflow[k]*w).sum() for k in su.index))
        nuclear=bool(((g.carrier=='nuclear')&g.p_nom_extendable&(g.p_nom_max>0)).any())
        out[c]=dict(demand_mwh=demand,renewable_potential_mwh=potential,ror_existing_mwh=hydro_e,reservoir_inflow_mwh=hydro_inflow,nuclear_candidate_unbounded=nuclear,zero_emission_supply_can_cover_demand=bool(nuclear or potential+hydro_e+hydro_inflow>=demand))
    return out

def main(a):
    import pypsa,logging
    logging.getLogger('pypsa').setLevel(logging.ERROR)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True);run=dict(label=a.label,scenario=a.scenario,authorization=a.authorization,solver=a.solver,started_epoch=time.time(),optimize_calls=0,retry=False)
    sampler=Sampler(out/'RESOURCE.jsonl');sampler.start()
    try:
        net_sha=sha(a.network);n=pypsa.Network(str(a.network))
        if n.meta.get('scenario')!=a.scenario:raise ValueError('Network scenario tag differs from --scenario')
        if a.truncate:
            sns=n.snapshots[:a.truncate];n.set_snapshots(sns)
            if a.label!='SMOKE_TEST_ONLY':raise ValueError('Truncated horizons are smoke tests only')
        n.meta.update(solver_allowed=True,artifact_role=a.label+'_UNSOLVED',s1_solve_authorization=a.authorization,s1_solve_label=a.label)
        from assembly_components import install_research_constraint_hooks
        if a.config_json:cfg=json.loads(Path(a.config_json).read_text())  # resolved config exported with the release (cloud has no upstream _helpers stack)
        else:
            from phase4_static import config
            cfg=config(a.repo,a.scenario)
        t0=time.time();m=n.optimize.create_model();install_research_constraint_hooks(n)
        hooks=sorted(k for k in m.constraints if k.startswith('research_') or k.startswith('Research'))
        lp_meta,M=export_lp(m,out/'lp');build_seconds=time.time()-t0
        run.update(input_network=dict(path=str(a.network),sha256=net_sha,snapshots=int(len(n.snapshots)),truncated_to=a.truncate),lp=dict(num_col=lp_meta['num_col'],num_row=lp_meta['num_row'],nnz=lp_meta['nnz'],build_seconds=build_seconds,research_constraints=hooks,country_limits=[k for k in hooks if 'co2_limit' in k]))
        save(out/'SOLVE_RECEIPT.json',run)
        if a.solver=='gurobi':
            params=dict(D5_GUROBI,TimeLimit=float(a.time_limit),LogFile=str(out/'gurobi.log'));io_api='direct'
        else:params=dict(threads=4,log_file=str(out/'highs.log'),time_limit=float(a.time_limit),solver='ipm' if a.highs_ipm else 'choose');io_api=None
        run['solver_parameters']=params;run['parameter_source']=D5_SOURCE if a.solver=='gurobi' else 'HiGHS defaults (smoke test only)'
        t1=time.time();run['optimize_calls']=1;save(out/'SOLVE_RECEIPT.json',run)
        status,condition=n.optimize.solve_model(solver_name=a.solver,solver_options=params,io_api=io_api,log_fn=str(out/(a.solver+'.linopy.log')))
        run.update(status=status,termination_condition=condition,solve_seconds=time.time()-t1)
        if a.solver=='gurobi' and m.solver_model is not None:
            sm=m.solver_model;run['effective_parameters']={k:sm.getParamInfo(k)[2] for k in D5_GUROBI if k!='LogToConsole'};run['native']=dict(Status=sm.Status,BarIterCount=sm.BarIterCount,IterCount=sm.IterCount,Runtime=sm.Runtime)
        if status!='ok':
            diag=dict(status=status,condition=condition,structural_supply=structural_supply_diagnosis(n))
            if a.solver=='gurobi' and condition=='infeasible':
                try:m.solver_model.computeIIS();m.solver_model.write(str(out/'infeasible.ilp'));diag['iis_file']=str(out/'infeasible.ilp')
                except Exception as e:diag['iis_error']=str(e)[:300]
            save(out/'INFEASIBILITY_DIAGNOSIS.json',diag);run['decision']='STOP_INFEASIBLE_OR_FAILED_NO_RELAXATION';save(out/'SOLVE_RECEIPT.json',run);print(json.dumps(dict(status=status,condition=condition)));return 2
        run['objective']=float(m.objective.value);run['objective_constant_excluded_sunk_capex']=float(getattr(n,'objective_constant',0.) or 0.)
        sol_dir=out/'solution';sol_dir.mkdir(exist_ok=True)
        X=np.asarray(M.sol,dtype='<f8');Pi=np.asarray(M.dual,dtype='<f8');rc_map=reduced_costs(m,a.solver)
        RC=np.array([rc_map.get(int(l),np.nan) for l in M.vlabels],dtype='<f8')
        if not np.isfinite(X).all() or not np.isfinite(Pi).all() or not np.isfinite(RC).all():raise ValueError('Incomplete primal/dual/reduced-cost vectors')
        for k,v in [('X',X),('Pi',Pi),('RC',RC)]:np.save(sol_dir/(k+'.npy'),v)
        run['solution']={k:dict(count=int(len(v)),sha256=sha(sol_dir/(k+'.npy'))) for k,v in [('X',X),('Pi',Pi),('RC',RC)]}
        # outputs
        from v5.v5_gates import load_contract,gate_a1_a2_kkt,gate_a3_a5_physics,gate_a4_readback,gate_a6_binding,gate_b1_country_net_zero,gate_b11_completeness,gate_b12_hash,capacity_reduced_costs,nodal_prices,cross_border_flows
        from country_carbon import emission_report
        n.meta['artifact_role']=a.label+'_SOLVED';n.meta['result_label']=a.label
        capacity_reduced_costs(n,m,rc_map).to_csv(out/'capacity_reduced_costs.csv',index=False)
        prices,full=nodal_prices(n);prices.to_csv(out/'nodal_prices_summary.csv',index=False);full.to_csv(out/'nodal_prices.csv')
        cross_border_flows(n).to_csv(out/'cross_border_flows.csv',index=False)
        emis=emission_report(n);save(out/'EMISSIONS_BY_COUNTRY.json',emis)
        caps={typ:n.df(typ).groupby(['carrier','country'])[nom+'_opt'].sum().reset_index().to_dict('records') for typ,nom in [('Generator','p_nom'),('Link','p_nom'),('StorageUnit','p_nom'),('Store','e_nom')] if 'country' in n.df(typ)}
        save(out/'CAPACITY_BY_TECH_COUNTRY.json',caps)
        contract=load_contract();gates={}
        gates['A1_A2']=gate_a1_a2_kkt(out/'lp',sol_dir,out/'v5',contract)
        a3,a5=gate_a3_a5_physics(n);gates['A3']=a3;gates['A5']=a5
        gates['A4']=gate_a4_readback(n,out/(a.scenario+'_'+a.label+'_solved.nc'))
        gates['A6']=gate_a6_binding(run,lp_meta,net_sha)
        gates['B1']=gate_b1_country_net_zero(n);gates['B11']=gate_b11_completeness(n,cfg);gates['B12']=gate_b12_hash(n,cfg)
        gates['contract']=dict(id=contract['contract_id'],status=contract['status'],result_label=contract['result_label'])
        gates['all_passed']=all(v['passed'] for k,v in gates.items() if isinstance(v,dict) and 'passed' in v)
        save(out/'V5_GATES.json',gates)
        run.update(gates={k:v['passed'] for k,v in gates.items() if isinstance(v,dict) and 'passed' in v},peak_rss_bytes=sampler.peak,finished_epoch=time.time(),solved_network=gates['A4']['file'],decision='SOLVED_'+a.label)
        save(out/'SOLVE_RECEIPT.json',run);print(json.dumps(dict(status=status,objective=run['objective'],gates=run['gates'],peak_rss_gib=round(sampler.peak/2**30,2))));return 0
    except BaseException as e:
        run.update(failure=dict(error=type(e).__name__,detail=str(e)[:2000],traceback=traceback.format_exc()[-4000:]),peak_rss_bytes=sampler.peak,finished_epoch=time.time());save(out/'SOLVE_RECEIPT.json',run);raise
    finally:sampler.stop.set()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=HERE.parent);p.add_argument('--network',type=Path,required=True);p.add_argument('--scenario',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--solver',choices=['highs','gurobi'],default='highs');p.add_argument('--truncate',type=int,default=0);p.add_argument('--label',default='SMOKE_TEST_ONLY');p.add_argument('--authorization',required=True);p.add_argument('--time-limit',type=float,default=3600.);p.add_argument('--highs-ipm',action='store_true');p.add_argument('--config-json',type=Path,default=None)
    sys.exit(main(p.parse_args()))
