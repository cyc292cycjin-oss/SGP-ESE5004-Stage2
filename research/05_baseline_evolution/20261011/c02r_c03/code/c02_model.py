"""C02 assembly and streamed LP export. No solver binding is imported here."""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import csv,math,json,copy,gc,hashlib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from c02_common import read,write,sha
from c02_semantics import rhs_exact,bounds_exact
from c02_zero_rows import certify_network

def bits(a,b):
    a,b=np.asarray(a),np.asarray(b)
    if a.shape!=b.shape:raise ValueError('shape differs')
    if a.dtype.kind=='f' and b.dtype.kind=='f':
        if not np.array_equal(a.astype('<f8').view('<u8'),b.astype('<f8').view('<u8')):raise ValueError('binary64 differs')
    elif not np.array_equal(a,b):raise ValueError('values differ')
def arrsha(a):return hashlib.sha256(np.ascontiguousarray(a,dtype='<f8').tobytes()).hexdigest()
def average(a):
    a=np.asarray(a,dtype='<f8');assert a.shape==(2920,) and np.isfinite(a).all()
    if np.all(a.view('<u8')==a.view('<u8')[0]):return np.full(365,a[0],dtype='<f8')
    return np.array([float(sum(map(lambda x:F(float(x)),v),F(0))/8) for v in a.reshape(365,8)],dtype='<f8')
def exact_energy(a,h):return sum((F(float(x))*F(float(y)) for x,y in zip(a,h)),F(0))

def assemble_daily(source,root,out,progress):
    import pypsa
    from assembly_components import validate_hooks,check_global_constraints
    from fixed_accounts import validate_exported_accounting
    n=pypsa.Network(source);assert len(n.snapshots)==2920 and len(n.loads)==1737
    expected=pd.date_range('2013-01-01',periods=2920,freq='3h',name='snapshot')
    assert n.snapshots.equals(expected)
    for col in ('objective','generators','stores'):bits(n.snapshot_weightings[col].to_numpy(),np.full(2920,3.))
    active={(c.name,k) for c in n.iterate_components() for k,f in c.pnl.items() if len(f.columns)}
    assert active=={('Load','p_set'),('Generator','p_max_pu'),('StorageUnit','inflow')},('BLOCKED_PROTOCOL_EXTENSION',active)
    static={c.name:c.df.copy(deep=True) for c in n.iterate_components()};oldmeta=copy.deepcopy(n.meta)
    frames={k:n.pnl(k[0])[k[1]].copy(deep=True) for k in active}
    led=read(root/'c01r/C01R_LOAD_ROUNDING_LEDGER.json');loads={r['LoadID']:r for r in led['records']}
    cf=read(root/'c01r/C01_CF_INFLOW_ROUNDING_CHECK.json'); refs={('Load','p_set'):loads,
       ('Generator','p_max_pu'):{r['asset']:r for r in cf['CF']['records']},('StorageUnit','inflow'):{r['asset']:r for r in cf['inflow']['records']}}
    days=pd.DatetimeIndex(expected[::8].values,name='snapshot');daily={};aggregation=[]
    for key,frame in sorted(frames.items()):
        assert set(frame.columns)==set(refs[key])
        result=np.empty((365,len(frame.columns)),dtype='<f8')
        for i,name in enumerate(frame.columns):
            a=frame[name].to_numpy();assert np.isfinite(a).all() and (a>=0).all()
            d=average(a);r=refs[key][name];expected_hash=r['daily_audit_value_SHA256'] if key[0]=='Load' else r['daily_simulation_SHA256_float64_LE']
            assert arrsha(d)==expected_hash,(key,name,'C01R accepted daily hash differs')
            result[:,i]=d
        daily[key]=pd.DataFrame(result,index=days,columns=frame.columns)
        aggregation.append({'component':key[0],'attribute':key[1],'assets':len(frame.columns),'accepted_value_hashes_matched':True})
        progress('AGGREGATED_'+key[0])
    # Only mutate this freshly loaded independent in-memory network.
    n.set_snapshots(days);n.snapshot_weightings.loc[:,['objective','generators','stores']]=24.
    for (comp,attr),df in daily.items():n.pnl(comp)[attr]=df
    scheme=read(root/'scheme_a/carrier_fragment.json');account=read(root/'scheme_a/external_pending_fixed_accounts.json')
    delta=read(root/'scheme_a/EXACT_SOURCE_CLOSURE_A_CHANGESET.json');changes={r['asset']:r for r in delta['changes']}
    assert len(changes)==180 and len(account)==807
    external={a['FixedAccountID']:a for a in account};oldexternal={a['FixedAccountID']:a for a in n.meta['external_pending_fixed_accounts']}
    assert set(external)==set(oldexternal)==set(n.meta['biomass_obligation_routes'])
    changed=[]
    for asset,a in external.items():
        q=float(a['QuantityMWh']);old=float(n.stores.at[asset,'e_nom']);params=scheme['components']['Store:'+asset]['params'];route=scheme['biomass_obligation_routes'][asset]
        assert q==float(params['e_nom'])==float(params['e_initial'])==float(route['annual_cap_mwh'])>0
        check=copy.deepcopy(oldexternal[asset]);check['QuantityMWh']=q;assert check==a,('external non-Q change',asset)
        oldroute=copy.deepcopy(n.meta['biomass_obligation_routes'][asset]);oldroute['annual_cap_mwh']=q;assert oldroute==route,('route non-Q change',asset)
        assert float(n.stores.at[asset,'e_initial'])==old==float(oldexternal[asset]['QuantityMWh'])
        if asset in changes:
            assert old.hex()==changes[asset]['before_hex'] and q.hex()==changes[asset]['after_hex'];changed.append(asset)
        else:assert old.hex()==q.hex()
        n.stores.loc[asset,['e_nom','e_initial']]=q
        n.meta['biomass_obligation_routes'][asset]['annual_cap_mwh']=q
    n.meta['external_pending_fixed_accounts']=account
    # All static frames and all scientific metadata have an explicit two-field/four-field whitelist.
    for c in n.iterate_components():
        e=static[c.name].copy(deep=True)
        if c.name=='Store':
            for asset in changed:e.loc[asset,['e_nom','e_initial']]=external[asset]['QuantityMWh']
        pd.testing.assert_frame_equal(e,c.df,check_exact=True)
    approvedmeta=copy.deepcopy(oldmeta);approvedmeta['external_pending_fixed_accounts']=account
    for asset in changed:approvedmeta['biomass_obligation_routes'][asset]['annual_cap_mwh']=external[asset]['QuantityMWh']
    assert n.meta==approvedmeta
    groups=[]
    for g in led['Scheme_A_groups']:
        demand=exact_energy(n.loads_t.p_set[g['LoadID']],n.snapshot_weightings.stores)
        q=sum((F(float(external[s]['QuantityMWh'])) for s in g['account_ids']),F(0))
        assert demand==F(g['D_original_MWh'])==F(g['D_daily_MWh']) and q==F(g['Q_prime_MWh']) and demand<=q
        groups.append({'load':g['LoadID'],'D':str(demand),'Q':str(q),'slack':str(q-demand),'accounts':g['account_ids']})
    assert len(groups)==385
    validate_hooks(n);check_global_constraints(n);validate_exported_accounting(n)
    # Provenance-only new fields; scientific metadata remains intact.
    n.meta.update(artifact_role='C02_DAILY_UNSOLVED',solver_allowed=False,C02_scheme_a_sha=sha(root/'scheme_a/EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json'),C02_protocol_sha=sha(root/'c01r/C00_DAILY_365_PROTOCOL_C01R_V1.md'))
    path=out/'daily_365_unsolved.nc';n.export_to_netcdf(path);progress('NETWORK_EXPORTED')
    loaded=pypsa.Network(path)
    assert loaded.meta==n.meta and loaded.snapshots.equals(days)
    pd.testing.assert_frame_equal(n.snapshot_weightings,loaded.snapshot_weightings,check_exact=True,check_freq=False)
    for c in n.iterate_components():
        pd.testing.assert_frame_equal(c.df,loaded.df(c.name),check_exact=True,check_dtype=False,check_like=True)
        for attr,f in c.pnl.items():
            if len(f.columns):pd.testing.assert_frame_equal(f,loaded.pnl(c.name)[attr],check_exact=True,check_dtype=False,check_freq=False,check_like=True)
    for col in loaded.snapshot_weightings:assert float(loaded.snapshot_weightings[col].sum())==8760
    write(out/'C02_NETWORK_LP_DIFF_REGISTER.json',{'status':'NETWORK_WHITELIST_PASS_LP_PENDING','changes':changed,'changed_accounts':180,'unchanged_accounts':627,
       'static_nonwhitelist_changes':0,'scientific_metadata_nonwhitelist_changes':0,'Load_daily':'matches pinned C01R asset hashes','objective_cost_fields':'UNCHANGED','ports_efficiencies_policies':'UNCHANGED',
       'new_provenance_metadata':['artifact_role','solver_allowed','C02_scheme_a_sha','C02_protocol_sha'],'not_equivalent_to_2920_LP':True})
    write(out/'SCHEME_A_DAILY_EXACT_GROUPS.json',{'status':'PASS','groups':groups,'source_Q_rederived':False})
    write(out/'NETWORK_READBACK.json',{'status':'EXACT_VALUES_PASS','path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'snapshots':365,'weight_sums':{k:8760 for k in loaded.snapshot_weightings},'aggregation':aggregation,'representation_error_deducted_from_V4':False})
    del n,frames,static;gc.collect();return loaded,led

def add_hooks(n):
    """C02-only dispatch of frozen pure constraint functions; no production solver entry."""
    from assembly_components import validate_hooks,check_global_constraints
    from fixed_accounts import validate_exported_accounting
    from carrier_architecture import install_fragment_constraints
    from build_only_extracted import install_existing_asset_constraints
    assert n.meta['artifact_role']=='C02_DAILY_UNSOLVED' and n.meta['solver_allowed'] is False
    validate_hooks(n);check_global_constraints(n);validate_exported_accounting(n)
    before=set(n.model.constraints)
    install_fragment_constraints(n)
    if n.meta.get('existing_unit_components'):install_existing_asset_constraints(n)
    for i,p in enumerate(n.meta['battery_inverter_pairs']):
        a,b=p['charger'],p['discharger'];eff=float(n.links.at[b,'efficiency'])
        n.model.add_constraints(n.model['Link-p_nom'].sel({'Link-ext':a})-eff*n.model['Link-p_nom'].sel({'Link-ext':b})==0,name='ResearchBatteryNominal-'+str(i))
    required={'ResearchStoreDirection-'+s for s in n.meta['store_power_rules']}
    required|={'ResearchBatteryNominal-'+str(i) for i in range(len(n.meta['battery_inverter_pairs']))}
    required|={'ResearchImportAnnual-'+s for s in n.meta.get('external_annual_caps',{})}
    required|={'ResearchExistingResource-'+s for s,g in n.meta.get('existing_resource_groups',{}).items() if g['candidates']}
    assert set(n.model.constraints)-before==required and len(n.meta['store_power_rules'])==807 and len(n.meta['battery_inverter_pairs'])==196
    return before

def canonical_rows(m,vmap,progress):
    for name,block in m.constraints.items():
        for part in block.iterate_slices(slice_size=100000):
            f=part.flat
            if f.empty:continue
            rows=f.drop_duplicates('labels');cl=rows.labels.to_numpy(dtype=np.int64)
            assert np.all(np.diff(cl)>0)
            rowidx=np.searchsorted(cl,f.labels.to_numpy());cols=vmap[f.vars.to_numpy(dtype=int)];assert np.all(cols>=0)
            a=csr_matrix((f.coeffs.to_numpy(dtype=np.float64),(rowidx,cols)),shape=(len(cl),len(vmap[vmap>=0])))
            a.sum_duplicates();a.sort_indices();a.eliminate_zeros()
            rhs=rows.rhs.to_numpy(dtype=np.float64);signs=rows.sign.to_numpy();assert np.isin(signs,['=','<=','>=']).all()
            lower=np.where(signs!='<=',rhs,-np.inf);upper=np.where(signs!='>=',rhs,np.inf)
            yield name,cl,a,lower,upper
        progress('EXPORT_'+name)

def family(name):
    for prefix in ('ResearchStoreDirection','ResearchBatteryNominal','ResearchImportAnnual','ResearchExistingResource'):
        if name.startswith(prefix+'-'):return prefix
    return name

def objectives(n,root,vl,vmap,c):
    rows=list(csv.DictReader((root/'EFFECTIVE_PERTURBATION_LEDGER.csv').open()));table={(r['component'],r['asset_id'],r['field']):r for r in rows};adapt=c.copy();offset=[]
    for r in rows:
        df=n.df(r['component']);assert r['asset_id'] in df.index
        assert float(df.at[r['asset_id'],r['field']]).hex()==float(r['base_model_coefficient']).hex()
        if r['field']=='capital_cost':
            nom={'Line':'s_nom','Link':'p_nom'}[r['component']]
            if df.at[r['asset_id'],nom+'_extendable']:
                offset.append((float(r['adapted_model_coefficient'])-float(r['base_model_coefficient']))*float(df.at[r['asset_id'],nom]))
    handled=[]
    for name,var in n.model.variables.items():
        if name.startswith('Research-') or name=='objective_constant':continue
        comp,attr=name.split('-',1);df=n.df(comp)
        if attr in ['p_nom','s_nom','e_nom']:
            ids=n.get_extendable_i(comp);original=df.loc[ids,'capital_cost'].to_numpy();new=np.array([float(table[(comp,s,'capital_cost')]['adapted_model_coefficient']) if (comp,s,'capital_cost') in table else float(df.at[s,'capital_cost']) for s in ids])
        elif name in ['Generator-p','Link-p','Store-p','StorageUnit-p_dispatch']:
            original=n.snapshot_weightings.objective.to_numpy()[:,None]*df.marginal_cost.to_numpy()[None,:]
            new=n.snapshot_weightings.objective.to_numpy()[:,None]*np.array([float(table[(comp,s,'marginal_cost')]['adapted_model_coefficient']) for s in df.index])[None,:]
        else:
            lab=var.labels.values;pos=vmap[lab[lab>=0]];assert np.all(c[pos]==0),('unhandled objective',name);continue
        lab=var.labels.values;mask=lab>=0;pos=vmap[lab[mask]];bits(c[pos],np.asarray(original)[mask]);adapt[pos]=np.asarray(new)[mask];handled.append(name)
    fom=n.model['Research-existing-FOM-constant'];pos=vmap[int(fom.labels.item())]
    assert float(c[pos])==float(n.meta['existing_annual_fixed_om_eur']) and adapt[pos]==c[pos]
    base_offset=float(n.model.objective.expression.const.item());assert base_offset==0
    return adapt,base_offset-math.fsum(offset),{'asset_ledger_sha256':sha(root/'EFFECTIVE_PERTURBATION_LEDGER.csv'),'reused_draws':True,'resampling':False,
      'offset_recomputed':True,'offset_terms':len(offset),'capital_offset_delta':-math.fsum(offset),'FOM_column':int(pos),'FOM_once_EUR':float(c[pos]),'handled_variables':handled,'NULL_prices_imputed':False}

def export_model(n,root,out,progress):
    m=n.model;assert m.type=='LP';v4=read(root/'V4_APPROVED.json');allowed=set(v4['constraint_blocks'])
    actual=set(map(family,m.constraints));assert actual==allowed,('unknown/missing families',actual-allowed,allowed-actual)
    target=out/'lp';target.mkdir(exist_ok=False);mapping=out/'mapping';mapping.mkdir(exist_ok=False)
    vf=m.variables.flat;vl=vf.labels.to_numpy(dtype=np.int64);assert len(vl)==m.nvars and np.all(np.diff(vl)>0)
    vm=np.full(m.shape[1],-1,dtype=np.int32);vm[vl]=np.arange(len(vl),dtype=np.int32)
    lb=vf.lower.to_numpy(dtype=float);ub=vf.upper.to_numpy(dtype=float);obj=m.objective.flat;c=np.zeros(len(vl));p=vm[obj.vars.to_numpy(dtype=int)];assert np.all(p>=0);np.add.at(c,p,obj.coeffs.to_numpy())
    adapted,offset,costmeta=objectives(n,root,vl,vm,c)
    audit=read(root/'GATE6_3H_ROUNDING_AUDIT.json');groups=audit['groups'];assert len(groups)==385
    vg=np.full(len(vl),-1,dtype=np.int32);D=np.ones(len(vl));owner=set()
    for g in groups:
        s=g['stores'];buses=n.stores.loc[s,'bus'];links=n.links.index[n.links.bus0.isin(buses)];assert len(links)==len(s)
        for name,dim,ids in [('Store-e','Store',s),('Store-p','Store',s),('Link-p','Link',links),('Link-p_nom','Link-ext',links)]:
            labs=m[name].labels.sel({dim:ids}).values.ravel();assert (labs>=0).all();pos=vm[labs];assert (vg[pos]==-1).all()
            vg[pos]=g['group'];D[pos]=g['scale']
        owner.update(s)
    assert len(owner)==807 and np.all(c[vg>=0]==0) and np.all(adapted[vg>=0]==0)
    arrays={'vlabels':vl,'col_lower_original':lb,'col_upper_original':ub,'cost_scientific_original':c,'cost_V3_original':adapted,
       'col_lower_scaled':lb/D,'col_upper_scaled':ub/D,'cost_scientific_scaled':c*D,'cost_V3_scaled':adapted*D,'D':D}
    bits(arrays['col_lower_scaled']*D,lb);bits(arrays['col_upper_scaled']*D,ub);bits(arrays['cost_V3_scaled']/D,adapted)
    files={}
    for name,a in arrays.items():
        path=target/(name+'.npy');np.save(path,a,allow_pickle=False);bits(np.load(path,mmap_mode='r'),a);files[name]={'file':path.name,'sha256':sha(path),'bytes':path.stat().st_size,'dtype':str(a.dtype),'shape':list(a.shape)}
    del vf,obj,arrays;gc.collect()
    coordinates={'variables':[],'constraints':[]}
    for kind,blocks in [('variables',m.variables),('constraints',m.constraints)]:
        for i,(name,b) in enumerate(blocks.items()):
            labels=b.labels.values;path=mapping/(kind+'_'+str(i)+'.npy');np.save(path,labels,allow_pickle=False);bits(np.load(path,mmap_mode='r'),labels)
            coordinates[kind].append({'name':name,'shape':list(labels.shape),'dims':list(b.labels.dims),'labels_file':path.name,'sha256':sha(path),
                'coordinates':{d:[str(x) for x in b.labels.get_index(d)] for d in b.labels.dims},'type':'continuous' if kind=='variables' else 'linear'})
    write(mapping/'LABELS.json',coordinates)
    chunks=[];counts=Counter();countnnz=Counter();seen=np.zeros(m.shape[0],dtype=bool);bounds={};total=0
    failure_path=out/'C02R_SEMANTIC_FAILURE.json'
    # These are the actual model row labels/values, later rechecked from exported chunks.
    for asset in sorted(owner):
        row=m.constraints['Store-energy_balance'].labels.sel(Store=asset).values;rhs=m.constraints['Store-energy_balance'].rhs.sel(Store=asset).values;q=float(n.stores.at[asset,'e_initial'])
        b=m.constraints['Store-energy_balance']
        signs=b.sign.broadcast_like(b.rhs).sel(Store=asset).values
        rhs_exact(rhs,np.r_[-q,np.zeros(364)],actual_signs=signs,expected_sign='=',asset_id=asset,family='Store-energy_balance',row_labels=row,report_path=failure_path)
        bounds[int(row[0])]=(-q,-q,'initial:'+asset)
        for nm,val in [('Store-fix-e-lower',0.),('Store-fix-e-upper',q)]:
            b=m.constraints[nm];dim=next(d for d in b.labels.dims if d!='snapshot');lab=b.labels.sel({dim:asset}).values;rr=b.rhs.sel({dim:asset}).values
            signs=b.sign.broadcast_like(b.rhs).sel({dim:asset}).values
            rhs_exact(rr,np.full(365,val),actual_signs=signs,expected_sign='>=' if nm=='Store-fix-e-lower' else '<=',asset_id=asset,family=nm,row_labels=lab,report_path=failure_path)
            # All 365 store bounds are checked in the persisted arrays below.
            for x in lab:bounds[int(x)]=(val,np.inf,'lower:'+asset) if val==0 else (-np.inf,val,'upper:'+asset)
    # All final-obligation Bus rows, exact daily RHS, not only the old certificate group.
    led=read(out/'SCHEME_A_DAILY_EXACT_GROUPS.json')
    for g in led['groups']:
        bus=n.loads.at[g['load'],'bus'];matched=[]
        for nm in ('Bus-nodal_balance','Bus-meshed-nodal_balance'):
            b=m.constraints[nm];dim=next(d for d in b.labels.dims if d!='snapshot')
            if bus in b.labels.get_index(dim):matched.append((nm,b,dim))
        assert len(matched)==1
        nm,b,dim=matched[0];lab=b.labels.sel({dim:bus}).values;rr=b.rhs.sel({dim:bus}).values;dd=n.loads_t.p_set[g['load']].to_numpy()
        signs=b.sign.broadcast_like(b.rhs).sel({dim:bus}).values
        rhs_exact(rr,dd,actual_signs=signs,expected_sign='=',asset_id=bus,family=nm,row_labels=lab,report_path=failure_path)
        for x,v in zip(lab,dd):bounds[int(x)]=(float(v),float(v),'final_bus:'+bus)
    matchedbounds=0
    for name,cl,a,lower,upper in canonical_rows(m,vm,progress):
        assert not seen[cl].any();seen[cl]=True
        for j,l in enumerate(cl):
            if int(l) in bounds:
                x,y,why=bounds[int(l)]
                bounds_exact(np.array([lower[j]]),np.array([upper[j]]),np.array([x]),np.array([y]),asset_id=why.split(':',1)[1],family=name,row_labels=np.array([l]),report_path=failure_path)
                matchedbounds+=1
        k=len(chunks);dir=target/('chunk_%05d'%k);dir.mkdir();nz=np.diff(a.indptr);assert (nz>0).all()
        gids=vg[a.indices];rg=gids[a.indptr[:-1]];assert np.array_equal(gids,np.repeat(rg,nz)),'mixed fixed-group row'
        R=np.ones(len(cl));mask=rg>=0;scales=np.array([g['scale'] for g in groups]);R[mask]=1/scales[rg[mask]]
        factor=D[a.indices]*np.repeat(R,nz);scaled=a.data*factor;bits(scaled/factor,a.data)
        values={'clabels':cl,'indptr':a.indptr,'indices':a.indices,'value_original':a.data,'value_scaled':scaled,'row_lower_original':lower,'row_upper_original':upper,
          'row_lower_scaled':lower*R,'row_upper_scaled':upper*R,'R':R}
        bits(values['row_lower_scaled']/R,lower);bits(values['row_upper_scaled']/R,upper)
        entries={}
        for key,val in values.items():
            p=dir/(key+'.npy');np.save(p,val,allow_pickle=False);bits(np.load(p,mmap_mode='r'),val);entries[key]={'sha256':sha(p),'bytes':p.stat().st_size}
        chunks.append({'dir':dir.name,'family':name,'rows':len(cl),'nnz':int(a.nnz),'arrays':entries});counts[family(name)]+=len(cl);countnnz[family(name)]+=int(a.nnz);total+=a.nnz
        if sum(p.stat().st_size for p in dir.iterdir())>512*1024**2:raise MemoryError('unexpected chunk size')
        del a,values,scaled;gc.collect()
    assert sum(c['rows'] for c in chunks)==m.ncons and matchedbounds==len(bounds)
    coverage=[];zero_evidence=[]
    for fam in sorted(allowed):
        names=[x for x in m.constraints if family(x)==fam];assert len(names)==v4['constraint_blocks'][fam]
        if counts[fam]==0:zero_evidence.append(certify_network(n,fam))
        source='source/carrier_architecture.py:283-303' if fam=='ResearchStoreDirection' else 'C02 add_hooks: frozen assembly_components.py:110-113' if fam=='ResearchBatteryNominal' else 'PyPSA 0.30.3 optimization/constraints.py or global_constraints.py'
        coverage.append({'family':fam,'blocks':len(names),'rows':counts[fam],'nnz':countnnz[fam],'source':source,'variable_type':'continuous','status':'ACTUAL_EXPORTED_READBACK_PASS'})
    write(out/'C02_CONSTRAINT_COVERAGE.json',{'status':'PASS','families':coverage,'zero_row_families':zero_evidence,
      'optional_absent':{'ResearchImportAnnual':'frozen external_annual_caps empty','ResearchExistingResource':'frozen groups have no candidates'},'known_FOM_once':costmeta['FOM_once_EUR'],'solver_called':False})
    record={'version':'C02_DAILY_CHUNKED_CSR_LP','status':'EXACT_NUMPY_EXPORT_READBACK_PASS','rows':int(m.ncons),'columns':int(m.nvars),'nnz':int(total),
      'sense':'min','arrays':files,'chunks':chunks,'scientific_offset':0.,'V3_offset':offset,'objective':costmeta,'coordinate_rule':'FIRST_GATE6_FIXED_INVENTORY_GROUP_POWER_OF_TWO; alpha=1',
      'matrix':'A_scaled=R A_original D','primal':'x_original=D z','dual':'y_original=R y_scaled','reduced_cost':'rc_original=rc_scaled/D',
      'scheme_A_actual_exported_row_bounds_checked':matchedbounds,'network_sha256':sha(out/'daily_365_unsolved.nc'),'label_manifest_sha256':sha(mapping/'LABELS.json'),'no_native_model_created':True}
    write(target/'MATH_PROBLEM.json',record)
    diff=read(out/'C02_NETWORK_LP_DIFF_REGISTER.json');diff.update(status='BUILD_STATIC_DIFF_WHITELIST_PASS',actual_LP_source_bounds='PASS',daily_objectives='REGENERATED_FROM_SAME_ASSET_LEDGER',full_2920_matrix_rebuilt=False);write(out/'C02_NETWORK_LP_DIFF_REGISTER.json',diff)
    return record
