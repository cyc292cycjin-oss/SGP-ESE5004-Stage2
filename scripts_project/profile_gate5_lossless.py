"""365-snapshot BUILD/TRANSFER ONLY. Hard prohibition on run/presolve calls."""
import argparse, csv, gc, json, os, resource, subprocess, threading, time, weakref
from pathlib import Path
import numpy as np
import pandas as pd
import psutil, pypsa, linopy, highspy
from unittest.mock import patch
from precision_handoff import transfer
from fixed_inventory_scaling import FixedInventoryScaling
from inventory_audit import audit
from assembly_components import install_research_constraint_hooks, validate_hooks, check_global_constraints
from fixed_accounts import validate_exported_accounting
from run_gate5_validation import hook_receipt
from gate5_resources import sha, host_read
from lossless_gate5_lifecycle import save_mapping, trim, bounded_build_allocator, explicit_empty_dask_chunks

FROZEN = '7a07a0ec728b7cc4b9b27a4a2461b67c960790750fd45eed6a3705624c8e06cd'


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


class Profile:
    def __init__(self, out, host):
        self.out, self.host, self.phase = out, host, 'startup'
        self.started = time.monotonic()
        self.events = []
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.monitor, daemon=True)
        self.thread.start()

    def sample(self):
        return dict(elapsed_s=time.monotonic()-self.started, phase=self.phase,
                    rss_bytes=psutil.Process().memory_info().rss,
                    peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                    guest_available_bytes=psutil.virtual_memory().available,
                    swap_used_bytes=psutil.swap_memory().used)

    def monitor(self):
        with (self.out/'MEMORY_SAMPLES.jsonl').open('w', buffering=1) as f:
            while not self.stop.wait(0.2):
                r = self.sample()
                try:
                    # DrvFS can briefly invalidate a name during an NTFS replace.
                    # Retry only that absence for at most 40 ms; retain the same
                    # timestamp, scope and memory checks on the actual sample.
                    for retry in range(3):
                        try:
                            host = host_read(self.host, max_age=35)
                            break
                        except FileNotFoundError:
                            if retry==2:raise
                            time.sleep(0.02)
                    r.update(host_available_bytes=host['physical_available_bytes'], host_commit_available_bytes=host['commit_available_bytes'])
                    reason = 'HOST_AVAILABLE_BELOW_2_GIB' if host['physical_available_bytes'] < 2*1024**3 else None
                    if host['commit_available_bytes'] < 512*1024**2:
                        reason = 'HOST_COMMIT_BELOW_512_MIB'
                except Exception as e:
                    reason = 'HOST_MONITOR_UNAVAILABLE_OR_STALE:' + str(e)
                if r['guest_available_bytes'] < 512*1024**2:
                    reason = 'GUEST_AVAILABLE_BELOW_512_MIB'
                f.write(json.dumps(r)+'\n')
                if reason:
                    dump(self.out/'RESOURCE_STOP.json', dict(reason=reason, last_sample=r, solver_runs=0))
                    os._exit(3)

    def mark(self, phase, **extra):
        self.phase = phase
        row = self.sample()
        row.update(extra)
        self.events.append(row)
        dump(self.out/'PHASE_EVENTS.json', self.events)
        print(phase, 'RSS MiB', round(row['rss_bytes']/1024**2, 2), flush=True)

    def close(self):
        self.stop.set()
        self.thread.join()


def ownership(n, scaling=None):
    """Targeted ownership census. These byte totals are not RSS savings."""
    arrays, pandas_objects, seen = [], [], set()
    def add(name, value):
        if not isinstance(value, np.ndarray):
            return
        owner = value
        while isinstance(owner.base, np.ndarray):
            owner = owner.base
        if id(owner) in seen:
            return
        seen.add(id(owner))
        if owner.nbytes >= 1024**2:
            arrays.append(dict(name=name, dtype=str(owner.dtype), shape=list(owner.shape), bytes=owner.nbytes))
    for component in n.iterate_components():
        for name, frame in [('static', component.df)] + list(component.pnl.items()):
            pandas_objects.append(dict(name=component.name+'.'+name, bytes=int(frame.memory_usage(index=True, deep=True).sum())))
            for block in frame._mgr.blocks:
                add(component.name+'.'+name, block.values)
    if n.model is not None:
        for kind in ['variables','constraints']:
            for name, block in getattr(n.model, kind).items():
                for key, value in block.data.variables.items():
                    # Do not materialize lazy Dask arrays for a census.
                    add(kind+'.'+name+'.'+key, value.data)
    if scaling is not None:
        for key, value in vars(scaling).items():
            add('scaling.'+key, value)
    return dict(large_unique_ndarray_owners=arrays,
                large_array_owner_bytes=sum(x['bytes'] for x in arrays),
                pandas_logical_bytes=sum(x['bytes'] for x in pandas_objects),
                pandas_largest=sorted(pandas_objects,key=lambda x:x['bytes'],reverse=True)[:20],
                note='Pandas logical totals overlap NumPy owners; not additive to RSS. No global sparse matrix is materialized. Transfer CSR scratch is chunk-local.',
                python_heap='Not globally traced during full model run to avoid changing its peak. Scoped heap tests are separate.')


class CountScaling(FixedInventoryScaling):
    def __init__(self, n, identity):
        super().__init__(n, identity)
        self.group_row_counts = np.zeros(len(self.groups), dtype=np.int64)

    def rows(self, cl, a, lower, upper):
        rg = self.vgroups[a.indices[a.indptr[:-1]]]
        self.group_row_counts += np.bincount(rg[rg>=0], minlength=len(self.groups))
        return super().rows(cl,a,lower,upper)


def projection(n, identity, scaling, out):
    rows=[]
    for g in identity['groups']:
        stores=g['stores']; buses=n.stores.loc[stores,'bus'].tolist(); final=g['final_buses']
        links=n.links.index[n.links.bus0.isin(buses)]
        variable_count=int((scaling.vgroups==g['group']).sum())
        constraint_count=int(scaling.group_row_counts[g['group']])
        exact_zero=g['exact_annual_difference']=='0'
        # Full streamed scaling already proved every touched matrix row belongs
        # entirely to one fixed group, and all its objective coefficients are 0.
        reasons=[]
        if len(stores)>1: reasons.append('MULTI_STOCK_TEMPORAL_FREEDOM_NOT_PROJECTED')
        if not exact_zero: reasons.append('EXACT_BINARY64_ANNUAL_NONZERO_OBLIGATION_MUST_REMAIN')
        reasons.append('REPORTING_AND_CAPACITY_RECONSTRUCTION_NOT_FORMALLY_PROVED')
        for s in stores:
            route=n.meta['biomass_obligation_routes'][s]
            rows.append(dict(group=g['group'], store=s, commodity=route['commodity'], source_row=route['source_row'],
                source_account_id=g['source_account_id'], final_load=g['load'], fixed_initial_mwh=n.stores.at[s,'e_initial'],
                stock_count_in_block=len(stores), solver_variables_in_block=variable_count, solver_constraints_in_block=constraint_count,
                matrix_isolation_verified=True, fixed_group_objective_zero_verified=True,
                exact_annual_difference=g['exact_annual_difference'], exact_annual_identity=exact_zero,
                eligible_for_implemented_projection=False, variables_saved=0, constraints_saved=0, memory_saved_bytes=0,
                exclusion=';'.join(reasons), block_counts_repeat_per_store=True))
    pd.DataFrame(rows).to_csv(out/'FIXED_BLOCK_PROJECTION_AUDIT.csv',index=False)
    dump(out/'PROJECTION_SUMMARY.json',dict(ledger_terms=len(rows),isolated_blocks=len(identity['groups']),
        single_stock_blocks=sum(len(g['stores'])==1 for g in identity['groups']),
        multi_stock_blocks=sum(len(g['stores'])>1 for g in identity['groups']),
        exact_zero_annual_blocks=sum(g['exact_annual_difference']=='0' for g in identity['groups']),
        formally_qualified_elimination_candidates=0,implemented_candidates=0,variables_saved=0,constraints_saved=0,
        estimated_memory_saved_bytes=0,scientific_obligations_deleted=0))


def no_solve(*args, **kwargs):
    raise AssertionError('No solver run or presolve is authorized in this study')


def run(root,out,host,build_chunk=None):
    out.mkdir(parents=True,exist_ok=False)
    profile=Profile(out,host)
    receipt=dict(solver_runs=0,presolve_calls=0,gate6_runs=0,phase5_runs=0,status='STARTED',
                 source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
                 build_chunk=build_chunk,snapshots=365)
    dump(out/'STUDY_RECEIPT.json',receipt)
    try:
        with patch.object(highspy.Highs,'run',no_solve), patch.object(highspy.Highs,'presolve',no_solve):
            if pypsa.__version__!='0.30.3' or linopy.__version__!='0.5.5' or highspy.Highs().version()!='1.11.0':
                raise ValueError('Frozen environment changed')
            source=root/'results_project/validation/gate5_20261006_01/research_2050_gate5_24h_validation_input.nc'
            if sha(source)!=FROZEN:raise ValueError('Frozen input changed')
            profile.mark('network_load_start')
            n=pypsa.Network(source)
            validate_hooks(n);check_global_constraints(n);validate_exported_accounting(n)
            assert len(n.snapshots)==365 and len(n.meta['external_pending_fixed_accounts'])==807
            identity=audit(n,root)
            prior=json.loads((root/'results_project/validation/gate5_20261006_04/FORMULATION_MAPPING_AND_ROUNDING_AUDIT.json').read_text())
            if identity!=prior:raise ValueError('Source identity audit changed')
            dump(out/'FORMULATION_MAPPING_AND_ROUNDING_AUDIT.json',identity)
            profile.mark('network_loaded')
            profile.mark('linopy_model_build')
            with bounded_build_allocator(), explicit_empty_dask_chunks():
                n.optimize.create_model(chunk=build_chunk);before=set(n.model.constraints)
                install_research_constraint_hooks(n)
            hooks=hook_receipt(n,before)
            assert len(hooks['research_constraint_names'])==1003
            dump(out/'CONSTRAINT_ATTACHMENT_RECEIPT.json',hooks)
            scaling=CountScaling(n,identity)
            profile.mark('linopy_model_complete',variables=int(n.model.nvars),constraints=int(n.model.ncons))
            dump(out/'OWNERSHIP_BUILD.json',ownership(n,scaling))
            certificate=json.loads((root/'research/04_model_assembly/final_validation/EXACT_LP_CONTRADICTION_ROWS.json').read_text())
            factors={k:v['factor'] for k,v in certificate.items()}
            labels=list(map(int,certificate))+[3459209,3459210]
            profile.mark('highs_transfer')
            native,mapping,fidelity=transfer(n.model,certificate_labels=labels,certificate_factors=factors,transformation=scaling)
            profile.mark('after_transfer_source_live')
            dump(out/'SOLVER_TRANSFER_FIDELITY.json',fidelity)
            old=json.loads((root/'results_project/validation/gate5_20261006_04/SOLVER_TRANSFER_FIDELITY.json').read_text())
            fields=['variables','constraints','nnz','variable_labels_sha256','constraint_labels_sha256',
                    'bounds_objective_sha256','objective_offset','objective_sense','constraint_blocks',
                    'original_to_solver_mapping','certificate_native_binary64_sum']
            comparison={k:fidelity[k]==old[k] for k in fields}
            if not all(comparison.values()):raise ValueError('Run04 mathematical identity comparison failed')
            dump(out/'RUN04_EQUIVALENCE.json',dict(status='PASS',comparison=comparison,baseline_sha256=sha(root/'results_project/validation/gate5_20261006_04/SOLVER_TRANSFER_FIDELITY.json')))
            dump(out/'OWNERSHIP_AFTER_TRANSFER.json',ownership(n,scaling))
            projection(n,identity,scaling,out)
            manifest=save_mapping(out/'mapping',n,mapping,scaling,source,FROZEN)
            profile.mark('mapping_persisted_source_live')
            # Frozen Linopy Model has __slots__ without __weakref__.
            # Track its GC identity, and weakrefs for the other two owners.
            nref,sref=weakref.ref(n),weakref.ref(scaling)
            model_id=id(n.model)
            assert gc.is_tracked(n.model)
            dimensions=(native.getNumCol(),native.getNumRow(),native.getNumNz())
            del n,mapping,scaling
            gc.collect()
            if any(r() is not None for r in [nref,sref]) or any(id(obj)==model_id and isinstance(obj,linopy.Model) for obj in gc.get_objects()):
                raise ValueError('Source owner still reachable')
            profile.mark('source_released_before_trim',source_weakrefs_dead=True)
            trim()
            profile.mark('source_released_after_trim',source_weakrefs_dead=True)
            if dimensions!=(native.getNumCol(),native.getNumRow(),native.getNumNz()):raise ValueError('Native dimensions changed after release')
            # Configure exact frozen options; do NOT call run or presolve.
            options={'threads':2,'time_limit':10800,'solver':'ipm','run_crossover':'on'}
            for k,v in options.items():
                if native.setOptionValue(k,v)!=highspy.HighsStatus.kOk:raise ValueError(k)
                if native.getOptionValue(k)[1]!=v:raise ValueError('Option mismatch: '+k)
            profile.mark('highs_solve_preparation_no_run',solver_live=True)
            # End-of-study destruction provides an empirical resident-model
            # increment, including native allocator effects, not internal workspace.
            native.clear();del native;trim()
            profile.mark('solver_released',solver_live=False)
            receipt.update(status='PASS_BUILD_TRANSFER_ONLY',input_sha256=sha(source),variables=dimensions[0],constraints=dimensions[1],nnz=dimensions[2],
                           solver_options=options,math_program_equivalent='PASS',source_lifetime_test='PASS',
                           solution_retrieval='NOT_RUN_NO_SOLVE',mapping='MOCK_TESTS_ONLY',validation='NOT_RUN_NO_SOLUTION',export='NOT_RUN_NO_SOLUTION',
                           scientific_model_changed=False,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
            dump(out/'STUDY_RECEIPT.json',receipt)
    except Exception as e:
        receipt.update(status='FAILED',error=repr(e))
        dump(out/'STUDY_RECEIPT.json',receipt)
        raise
    finally:
        profile.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);p.add_argument('--host-report',required=True);p.add_argument('--build-chunk',type=int)
    a=p.parse_args()
    import dask
    with dask.config.set(scheduler='synchronous'):
        run(Path(a.root),Path(a.output),Path(a.host_report),a.build_chunk)
