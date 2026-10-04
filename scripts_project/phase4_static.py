"""Read-only Phase4 validation hooks. Never assembles a model or calls optimize.

Conservation requires explicit independent control totals. Missing controls are
PENDING, not PASS. Sign exceptions and expected snapshot hours are caller inputs.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys
import numpy as np
import pandas as pd


def sha256(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def identity(repo, expected_commit, files):
    """files maps repo-relative paths to independent expected SHA256 values."""
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
    if actual != expected_commit:
        raise ValueError('Git identity mismatch')
    for path, digest in files.items():
        if sha256(Path(repo) / path) != digest:
            raise ValueError('Config/input hash mismatch: ' + path)
    return actual


def demand(frame, allow_negative=()):
    if frame.empty or not frame.index.is_unique or not frame.columns.is_unique:
        raise ValueError('Empty or duplicate demand identity')
    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('Non-finite demand')
    if (frame.drop(columns=list(allow_negative), errors='ignore').to_numpy(dtype=float) < 0).any():
        raise ValueError('Negative physical demand')
    return True


def conserve(expected, actual, atol=1e-6, rtol=1e-10):
    """Compare country/carrier or source/node MWh matrices with exact key sets."""
    demand(expected); demand(actual)
    if set(expected.index) != set(actual.index) or set(expected.columns) != set(actual.columns):
        raise ValueError('Conservation identity mismatch')
    aligned = actual.reindex(index=expected.index, columns=expected.columns)
    if not np.allclose(expected, aligned, atol=atol, rtol=rtol):
        raise ValueError('Annual conservation failed')
    return True


def allocation(expected, node_values, node_country):
    demand(node_values)
    if not node_country.index.is_unique or set(node_country.index) != set(node_values.index) or node_country.isna().any():
        raise ValueError('Node country mapping incomplete')
    return conserve(expected, node_values.groupby(node_country.reindex(node_values.index)).sum())


def snapshot_weights(network, expected_hours=None):
    w = network.snapshot_weightings
    if not network.snapshots.is_unique or len(network.snapshots) == 0 or not w.index.equals(network.snapshots):
        raise ValueError('Snapshot identity mismatch')
    if not {'objective', 'generators', 'stores'}.issubset(w.columns):
        raise ValueError('Missing weight role')
    if not np.isfinite(w.to_numpy()).all() or (w <= 0).any().any():
        raise ValueError('Non-positive or non-finite snapshot weights')
    if expected_hours is not None:
        for role, hours in expected_hours.items():
            if not np.isclose(w[role].sum(), hours, rtol=1e-10, atol=1e-8):
                raise ValueError('Represented-hours mismatch: ' + role)
    return {k: float(v) for k, v in w.sum().items()}


def annual_loads(network):
    snapshot_weights(network)
    if not network.loads.index.is_unique or not network.carriers.index.is_unique:
        raise ValueError('Duplicate Load/carrier identity')
    static = network.loads.p_set
    frame = pd.DataFrame(np.tile(static.to_numpy(), (len(network.snapshots), 1)),
                         index=network.snapshots, columns=static.index)
    dynamic = network.loads_t.p_set
    if not dynamic.columns.is_unique or not dynamic.index.equals(network.snapshots):
        raise ValueError('Load time-series identity mismatch')
    if not set(dynamic.columns).issubset(frame.columns):
        raise ValueError('Time series references missing Load')
    frame.loc[:, dynamic.columns] = dynamic
    if not np.isfinite(frame.to_numpy()).all():
        raise ValueError('Non-finite Load series')
    # Physical demand sign validation is separate: emission-accounting Loads
    # may intentionally be negative and require an explicit role contract.
    return frame.mul(network.snapshot_weightings.generators, axis=0).sum()


def bus_scope(name, row, country_overrides=None):
    overrides = country_overrides or {}
    country = overrides.get(name, row.get('country', ''))
    country = '' if pd.isna(country) else str(country)
    if country:
        return 'COUNTRY_SCOPED', country
    label = (str(name) + ' ' + str(row.get('location', ''))).lower()
    if any(x in label for x in ('earth', 'global', 'atmosphere')):
        return 'GLOBAL_SHARED', ''
    if any(x in label for x in ('regional', 'shared')):
        return 'REGIONAL_SHARED', ''
    return 'UNKNOWN', ''


def inventory(network, country_overrides=None):
    buses = {str(k): dict(scope=bus_scope(k, v, country_overrides)[0],
                         country=bus_scope(k, v, country_overrides)[1],
                         carrier=str(v.carrier)) for k, v in network.buses.iterrows()}
    edges, coupling, shared_components = [], [], []
    for component, table in [('Link', network.links), ('Line', network.lines), ('Transformer', network.transformers)]:
        for name, row in table.iterrows():
            ports = [str(row[k]) for k in table.columns if k.startswith('bus') and k[3:].isdigit() and pd.notna(row[k]) and str(row[k])]
            missing = [b for b in ports if b not in buses]
            countries = {buses[b]['country'] for b in ports if b in buses and buses[b]['country']}
            unknown = any(not buses[b]['country'] for b in ports if b in buses)
            shared = [b for b in ports if b in buses and buses[b]['scope'] in ['REGIONAL_SHARED','GLOBAL_SHARED']]
            classification = 'INVALID_ENDPOINT' if missing else ('SHARED_POOL' if shared else ('CROSS_BORDER' if len(countries)>1 else ('UNKNOWN' if unknown else 'DOMESTIC')))
            entry=dict(component=component,name=str(name),carrier=str(row.get('carrier','')),ports=ports,
                       countries=sorted(countries),classification=classification,missing=missing)
            edges.append(entry)
            if shared: shared_components.append(entry)
            if component=='Link' and len({buses[b]['carrier'] for b in ports if b in buses})>1:
                # Available conversion capacity, not dispatch/activity proof.
                entry=dict(entry,capacity_available=bool(row.get('p_nom',0)>0 or row.get('p_nom_extendable',False)))
                coupling.append(entry)
    for name,row in network.stores.iterrows():
        if str(row.bus) in buses and buses[str(row.bus)]['scope'] in ['REGIONAL_SHARED','GLOBAL_SHARED']:
            shared_components.append(dict(component='Store',name=str(name),ports=[str(row.bus)],carrier=str(row.carrier)))
    return dict(buses=buses,edges=edges,shared_components=shared_components,coupling=coupling,
                carriers=sorted(set(network.buses.carrier.astype(str))),
                policy_constraints=network.global_constraints.reset_index().to_dict('records'))


def preflight(network, controls=None):
    controls = controls or {}
    results = {}
    for key, call in [('G',lambda:snapshot_weights(network,controls.get('expected_hours'))),
                      ('B_C',lambda:annual_loads(network).to_dict())]:
        try: results[key]=dict(status='PASS',detail=call())
        except ValueError as exc: results[key]=dict(status='FAIL',detail=str(exc))
    # Independent input ledgers/sign and carbon-scope contracts are not inferred
    # from the network being tested. Call demand/conserve/allocation explicitly.
    for key in ['A','D','E','F','K']:
        results[key]=dict(status='PENDING',detail='Requires independent identity/sign/accounting/policy control')
    results['inventory']=inventory(network,controls.get('country_overrides'))
    results['full_sc_assembled']=False
    results['solver_status']='NOT_RUN'
    return results


def json_evidence(value):
    """Represent optional non-finite metadata explicitly, never as JSON NaN."""
    if isinstance(value, dict):
        return {str(k):json_evidence(v) for k,v in value.items()}
    if isinstance(value, list):
        return [json_evidence(v) for v in value]
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return str(value)
    return value


def config(repo, name='baseline'):
    """Resolve declared inputs with upstream deep merge/migrations; no Snakefile."""
    repo=Path(repo);sys.path.insert(0,str(repo/'scripts'))
    from _helpers import _deep_merge_dicts, migrate_config
    import yaml
    recipe=json.loads((repo/'configs/research/composition.json').read_text())
    value={}
    for rel in recipe['base_files']+recipe['identities'][name]:
        override=yaml.safe_load((repo/rel).read_text()) or {}
        value=_deep_merge_dicts(value,override)
    return migrate_config(value)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--network',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    import pypsa
    net=pypsa.Network(args.network)
    report=preflight(net);report['network_sha256']=sha256(args.network)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(json_evidence(report),indent=2,default=str,allow_nan=False))
    sys.exit(1 if any(isinstance(item,dict) and item.get('status')=='FAIL' for item in report.values()) else 0)
