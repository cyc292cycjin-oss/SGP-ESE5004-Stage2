"""Derive D-1 modules from the frozen C02R sources by explicit, minimal text patches; write unified diffs as evidence.

Every replacement must match exactly once, so a drifted source fails loudly.
"""
from pathlib import Path
import difflib

D = Path(__file__).resolve().parents[1] / 'release_d1'; O = D / '_c02r_original'


def patch(src, dst, edits):
    text = (O / src).read_text(encoding='utf-8'); new = text
    for old, rep in edits:
        assert new.count(old) == 1, (src, old[:80], new.count(old))
        new = new.replace(old, rep)
    (D / dst).write_text(new, encoding='utf-8')
    diff = ''.join(difflib.unified_diff(text.splitlines(True), new.splitlines(True), 'c02r_c03/code/' + src, 'release_d1/' + dst))
    (D.parent / 'evidence').mkdir(exist_ok=True)
    (D.parent / 'evidence' / ('DIFF_' + dst + '.patch')).write_text(diff, encoding='utf-8')


ASSEMBLE_OLD_START = 'def average(a):'
ASSEMBLE_OLD_END = 'def add_hooks(n):'
ASSEMBLE_NEW = '''def exact_energy(a,h):return sum((F(float(x))*F(float(y)) for x,y in zip(a,h)),F(0))

def assemble_2920(source,root,out,progress):
    """D-1: frozen 2920x3h network + Scheme A (180 Q revisions, 627 unchanged). No time aggregation, no C01R."""
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
    # Immutable Scheme A load/weight reference: every Load column and every weighting column, binary64 SHA.
    ref=read(root/'scheme_a/LOADS_AND_WEIGHTS_REFERENCE.json');assert ref['snapshots']==2920 and len(ref['loads'])==1737
    assert ref['network_reference']['sha256']==sha(source)
    for r in ref['loads']:assert arrsha(n.loads_t.p_set[r['LoadID']].to_numpy())==r['binary64_sha256'],('LOAD_REFERENCE',r['LoadID'])
    assert set(r['LoadID'] for r in ref['loads'])==set(n.loads.index)
    for col in ('objective','generators','stores'):assert arrsha(n.snapshot_weightings[col].to_numpy())==ref['weights_sha256']
    progress('LOADS_1737_REFERENCE_PASS')
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
    assert len(changed)==180 and len(external)-len(changed)==627
    # All static frames and all scientific metadata have an explicit two-field/four-field whitelist.
    for c in n.iterate_components():
        e=static[c.name].copy(deep=True)
        if c.name=='Store':
            for asset in changed:e.loc[asset,['e_nom','e_initial']]=external[asset]['QuantityMWh']
        pd.testing.assert_frame_equal(e,c.df,check_exact=True)
    # No dynamic attribute may change (no aggregation): every active time series bitwise identical.
    for (comp,attr),frame in frames.items():pd.testing.assert_frame_equal(frame,n.pnl(comp)[attr],check_exact=True)
    approvedmeta=copy.deepcopy(oldmeta);approvedmeta['external_pending_fixed_accounts']=account
    for asset in changed:approvedmeta['biomass_obligation_routes'][asset]['annual_cap_mwh']=external[asset]['QuantityMWh']
    assert n.meta==approvedmeta
    # 385 Scheme A groups on the native 3h horizon: exact D = sum p_set*3h, Q' = sum of revised accounts, D <= Q'.
    audit=read(root/'GATE6_3H_ROUNDING_AUDIT.json');assert audit['snapshots']==2920 and audit['source_input_sha256']==sha(source)
    groups=[];owned=[]
    for g in audit['groups']:
        demand=exact_energy(n.loads_t.p_set[g['load']],n.snapshot_weightings.stores)
        q=sum((F(float(external[s]['QuantityMWh'])) for s in g['stores']),F(0))
        assert demand<=q,('SCHEME_A_GROUP_D_GT_Q',g['load'])
        groups.append({'group':g['group'],'load':g['load'],'D':str(demand),'Q':str(q),'slack':str(q-demand),'accounts':g['stores'],'D_le_Q':True});owned+=g['stores']
    assert len(groups)==385 and len(owned)==len(set(owned))==807 and set(owned)==set(external)
    progress('SCHEME_A_385_EXACT_PASS')
    validate_hooks(n);check_global_constraints(n);validate_exported_accounting(n)
    # Provenance-only new fields; scientific metadata remains intact.
    n.meta.update(artifact_role='D1_2920_UNSOLVED',solver_allowed=False,D1_scheme_a_sha=sha(root/'scheme_a/EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json'),D1_source_network_sha=sha(source))
    path=out/'gate6_2920_scheme_a_unsolved.nc';n.export_to_netcdf(path);progress('NETWORK_EXPORTED')
    loaded=pypsa.Network(path)
    assert loaded.meta==n.meta and loaded.snapshots.equals(n.snapshots)
    pd.testing.assert_frame_equal(n.snapshot_weightings,loaded.snapshot_weightings,check_exact=True,check_freq=False)
    for c in n.iterate_components():
        pd.testing.assert_frame_equal(c.df,loaded.df(c.name),check_exact=True,check_dtype=False,check_like=True)
        for attr,f in c.pnl.items():
            if len(f.columns):pd.testing.assert_frame_equal(f,loaded.pnl(c.name)[attr],check_exact=True,check_dtype=False,check_freq=False,check_like=True)
    for col in loaded.snapshot_weightings:assert float(loaded.snapshot_weightings[col].sum())==8760
    for r in ref['loads']:assert arrsha(loaded.loads_t.p_set[r['LoadID']].to_numpy())==r['binary64_sha256']
    write(out/'D1_NETWORK_LP_DIFF_REGISTER.json',{'status':'NETWORK_WHITELIST_PASS_LP_PENDING','changes':changed,'changed_accounts':180,'unchanged_accounts':627,
       'static_nonwhitelist_changes':0,'scientific_metadata_nonwhitelist_changes':0,'dynamic_attributes_changed':0,'Load_2920':'all 1737 columns match Scheme A LOADS_AND_WEIGHTS_REFERENCE binary64 SHA',
       'objective_cost_fields':'UNCHANGED','ports_efficiencies_policies':'UNCHANGED','time_aggregation':'NONE','C01R_used':False,
       'new_provenance_metadata':['artifact_role','solver_allowed','D1_scheme_a_sha','D1_source_network_sha']})
    write(out/'SCHEME_A_2920_EXACT_GROUPS.json',{'status':'PASS','groups':groups,'group_count':385,'accounts':807,'snapshots':2920,'hours_per_snapshot':3,'source_Q_rederived':False})
    write(out/'NETWORK_READBACK.json',{'status':'EXACT_VALUES_PASS','path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'snapshots':2920,'weight_sums':{k:8760 for k in loaded.snapshot_weightings},
       'loads_reference_rechecked_after_readback':1737,'representation_error_deducted_from_V4':False})
    del n,frames,static;gc.collect();return loaded

'''

MODEL_EDITS = [
    ("\"\"\"C02 assembly and streamed LP export. No solver binding is imported here.\"\"\"",
     "\"\"\"D-1 2920 assembly and streamed LP export (derived from C02R c02_model.py). No solver binding is imported here.\"\"\""),
    ("    assert n.meta['artifact_role']=='C02_DAILY_UNSOLVED' and n.meta['solver_allowed'] is False",
     "    assert n.meta['artifact_role']=='D1_2920_UNSOLVED' and n.meta['solver_allowed'] is False"),
    ("    failure_path=out/'C02R_SEMANTIC_FAILURE.json'",
     "    failure_path=out/'D1_SEMANTIC_FAILURE.json';T=len(n.snapshots)"),
    ("rhs_exact(rhs,np.r_[-q,np.zeros(364)],", "rhs_exact(rhs,np.r_[-q,np.zeros(T-1)],"),
    ("rhs_exact(rr,np.full(365,val),", "rhs_exact(rr,np.full(T,val),"),
    ("    # All 365 store bounds are checked in the persisted arrays below.", "    # All T store bounds are checked in the persisted arrays below."),
    ("    # All final-obligation Bus rows, exact daily RHS, not only the old certificate group.\n    led=read(out/'SCHEME_A_DAILY_EXACT_GROUPS.json')",
     "    # All final-obligation Bus rows, exact 3h RHS, not only the old certificate group.\n    led=read(out/'SCHEME_A_2920_EXACT_GROUPS.json')"),
    ("    write(out/'C02_CONSTRAINT_COVERAGE.json',", "    write(out/'D1_CONSTRAINT_COVERAGE.json',"),
    ("    record={'version':'C02_DAILY_CHUNKED_CSR_LP',", "    record={'version':'D1_2920_CHUNKED_CSR_LP','snapshots':T,"),
    ("'network_sha256':sha(out/'daily_365_unsolved.nc')", "'network_sha256':sha(out/'gate6_2920_scheme_a_unsolved.nc')"),
    ("    diff=read(out/'C02_NETWORK_LP_DIFF_REGISTER.json');diff.update(status='BUILD_STATIC_DIFF_WHITELIST_PASS',actual_LP_source_bounds='PASS',daily_objectives='REGENERATED_FROM_SAME_ASSET_LEDGER',full_2920_matrix_rebuilt=False);write(out/'C02_NETWORK_LP_DIFF_REGISTER.json',diff)",
     "    diff=read(out/'D1_NETWORK_LP_DIFF_REGISTER.json');diff.update(status='BUILD_STATIC_DIFF_WHITELIST_PASS',actual_LP_source_bounds='PASS',objectives_V3='REGENERATED_FROM_SAME_ASSET_LEDGER',full_2920_matrix_built=T==2920);write(out/'D1_NETWORK_LP_DIFF_REGISTER.json',diff)"),
]

BINDING_EDITS = [
    ('"""Identity/time adaptation only. Scientific formulas stay in pinned V4 functions."""',
     '"""D-1 2920 V4 binding: identity/time re-binding only. Scientific formulas and thresholds stay in pinned V4."""'),
    ("from c02_model import family", "from d1_model import family"),
    ("    assert b['snapshots']==365 and b['annual_hours']==8760", "    assert b['snapshots']==b['expected_snapshots'] and b['annual_hours']==8760 and b['hours_per_snapshot']==3"),
    ("def make_binding(root,out,record):\n    v=read(root/'V4_APPROVED.json');coverage=read(out/'C02_CONSTRAINT_COVERAGE.json')\n    b={'binding_id':'DAILY_V4_C02_V1','parent_V4_SHA256':sha(root/'V4_APPROVED.json'),",
     "def make_binding(root,out,record,expected_snapshots=2920):\n    v=read(root/'V4_APPROVED.json');coverage=read(out/'D1_CONSTRAINT_COVERAGE.json')\n    b={'binding_id':'GATE6_2920_V4_D1_V1','parent_V4_SHA256':sha(root/'V4_APPROVED.json'),"),
    ("      'C01R_protocol_SHA256':sha(root/'c01r/C00_DAILY_365_PROTOCOL_C01R_V1.md'),\n      'network_SHA256':sha(out/'daily_365_unsolved.nc'),",
     "      'C01R_protocol_SHA256':None,'time_aggregation':'NONE',\n      'network_SHA256':sha(out/'gate6_2920_scheme_a_unsolved.nc'),"),
    ("'labels_SHA256':sha(out/'mapping/LABELS.json'),'snapshots':365,'source_year':2013,", "'labels_SHA256':sha(out/'mapping/LABELS.json'),'snapshots':record['snapshots'],'expected_snapshots':expected_snapshots,'hours_per_snapshot':3,'source_year':2013,"),
    ("'source_Q_and_Load_binding':'SCHEME_A_DAILY_EXACT_GROUPS.json',", "'source_Q_and_Load_binding':'SCHEME_A_2920_EXACT_GROUPS.json',"),
    ("'native_C_API':'C03_REQUIRED','optimization_authorized':False}", "'native_C_API':'D5_REQUIRED','optimization_authorized':False}"),
    ("    write(out/'DAILY_V4_BINDING.json',b);return b", "    write(out/'GATE6_2920_V4_BINDING.json',b);return b"),
]

BRIDGE_EDITS = [
    ('"""Lossless storage conversion of certified daily CSR chunks to legacy native CSC."""',
     '"""Lossless storage conversion of certified D-1 2920 CSR chunks to legacy native CSC (derived from daily_bridge.py)."""'),
    ("    assert m['version']=='C02_DAILY_CHUNKED_CSR_LP' and m['status']=='EXACT_NUMPY_EXPORT_READBACK_PASS' and m['sense']=='min'",
     "    assert m['version']=='D1_2920_CHUNKED_CSR_LP' and m['status']=='EXACT_NUMPY_EXPORT_READBACK_PASS' and m['sense']=='min'"),
    ("'same_scientific_problem_as_daily_CSR':True}", "'same_scientific_problem_as_2920_CSR':True,'snapshots':m['snapshots']}"),
    ("'row_ranges':row_ranges,'snapshots':365,'no_2920_label_reconstruction':True})",
     "'row_ranges':row_ranges,'snapshots':m['snapshots'],'labels_from_actual_build':True})"),
]

PC_EDITS = [
    ('"""Linux process protection. No solver imports and no network operations.',
     '"""Linux process protection (D-stage copy of the C07/C09 module; only phase_deadline reads phase budgets from the authorization). No solver imports and no network operations.'),
    (" if phase=='BUILD':return min(entered+1800,a['build_absolute_deadline_epoch'])\n if phase=='BRIDGE':return min(entered+900,a['load_absolute_deadline_epoch'])\n if phase=='NATIVE':return min(entered+3600,a['native_absolute_deadline_epoch'])\n if phase=='RAW_SAVE':return min(entered+300,a['raw_absolute_deadline_epoch'])\n if phase=='POSTPROCESS':return min(entered+1200,a['post_absolute_deadline_epoch'])",
     " if phase=='BUILD':return min(entered+a['build_phase_seconds'],a['build_absolute_deadline_epoch'])\n if phase=='BRIDGE':return min(entered+a['bridge_phase_seconds'],a['load_absolute_deadline_epoch'])\n if phase=='NATIVE':return min(entered+a['maximum_native_seconds'],a['native_absolute_deadline_epoch'])\n if phase=='RAW_SAVE':return min(entered+a['raw_save_seconds'],a['raw_absolute_deadline_epoch'])\n if phase=='POSTPROCESS':return min(entered+a['post_phase_seconds'],a['post_absolute_deadline_epoch'])"),
    (" command=['timeout','--signal=TERM','--kill-after='+str(a['term_grace_seconds'])+'s',str(remaining-a['term_grace_seconds'])+'s',sys.executable,str(HERE/'production_backup.py'),'seal',str(root)]",
     " raise RuntimeError('D stage seals through its own launcher; production_backup is not shipped')"),
    ("  with open(root/'guard.stdout.log','xb') as log:guard=subprocess.Popen([sys.executable,str(HERE/'production_control.py'),'guard',str(root/'GUARD_CONFIG.json')]",
     "  with open(root/'guard.stdout.log','xb') as log:guard=subprocess.Popen([sys.executable,str(HERE/'d_production_control.py'),'guard',str(root/'GUARD_CONFIG.json')]"),
]

if __name__ == '__main__':
    text = (O / 'c02_model.py').read_text(encoding='utf-8')
    i, j = text.index(ASSEMBLE_OLD_START), text.index(ASSEMBLE_OLD_END)
    # exact_energy is re-declared inside ASSEMBLE_NEW; the daily-only average()/assemble_daily() block is replaced.
    staged = text[:i] + ASSEMBLE_NEW + text[j:]
    (O / '_staged_model.py').write_text(staged, encoding='utf-8')
    patch('_staged_model.py', 'd1_model.py', MODEL_EDITS)
    (O / '_staged_model.py').unlink()
    full = (D / 'd1_model.py').read_text(encoding='utf-8')
    diff = ''.join(difflib.unified_diff(text.splitlines(True), full.splitlines(True), 'c02r_c03/code/c02_model.py', 'release_d1/d1_model.py'))
    (D.parent / 'evidence' / 'DIFF_d1_model.py.patch').write_text(diff, encoding='utf-8')
    patch('c02_binding.py', 'd1_binding.py', BINDING_EDITS)
    patch('daily_bridge.py', 'd1_bridge.py', BRIDGE_EDITS)
    patch('production_control_c09.py', 'd_production_control.py', PC_EDITS)
    print('ok')
