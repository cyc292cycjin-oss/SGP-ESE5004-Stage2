"""Apply isolated, evidence-based fixes and retain before/after regression evidence.

Run with the existing pypsa-earth Python in WSL. Never edits the tutorial checkout.
"""
from pathlib import Path
import ast, copy, hashlib, json, logging, os, shutil, subprocess, sys
from itertools import product
import numpy as np
import pandas as pd
import xarray as xr
import yaml
import rasterio
import rioxarray

HERE = Path(__file__).resolve().parent
BASE = Path(os.environ.get('ASEAN_PHASE2_ROOT', '/home/jin/research/SGP_ESE5004_Stage2/phase2'))
OLD = Path(os.environ.get('ASEAN_TUTORIAL_ROOT', str(BASE.parent/'pypsa-asean')))
ENV = {'pd': pd, 'np': np, 'xr': xr, 'os': os, 'rasterio': rasterio,
       'product': product, 'logger': logging.getLogger('review')}

def extract(path, names, env=None):
    namespace = dict(ENV, **(env or {}))
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(nodes) == len(names), (path, names)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias('annotations')], level=0), *nodes], type_ignores=[])), str(path), 'exec'), namespace)
    return namespace

def replace_function(path, name, replacement):
    source = path.read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = source.splitlines(keepends=True)
    path.write_text(''.join(lines[:node.lineno-1]) + replacement.rstrip()+'\n' + ''.join(lines[node.end_lineno:]))

ALLOCATOR = '''def country_to_nodal(industrial_production, keys):
    """Allocate each national quantity without changing its country total.

    Facility weights are preferred; a country with no facility weight uses the
    existing GDP fallback. Missing or invalid GDP is an error, never a zero demand.
    """
    if not keys.index.is_unique or not industrial_production.index.is_unique:
        raise ValueError("Industrial inputs require unique node and country indices")
    if keys.country.isna().any():
        raise ValueError("Industrial nodes have missing country identifiers")
    missing = set(keys.country) - set(industrial_production.index)
    unlocated = set(industrial_production.index) - set(keys.country)
    if missing or unlocated:
        raise ValueError(f"Industrial country mismatch: missing totals={missing}, missing nodes={unlocated}")
    nodal_production = pd.DataFrame(index=keys.index, columns=industrial_production.columns, dtype=float)
    for country, sector in product(industrial_production.index, industrial_production.columns):
        buses = keys.index[keys.country == country]
        mapping = sector if sector in keys.columns else "gdp"
        key = pd.to_numeric(keys.loc[buses, mapping], errors="raise")
        if key.isna().any() or (~key.map(lambda x: float("-inf") < x < float("inf"))).any() or (key < 0).any():
            raise ValueError(f"Invalid industrial weights for {country}/{sector}/{mapping}")
        if key.sum() == 0 and mapping != "gdp":
            key = pd.to_numeric(keys.loc[buses, "gdp"], errors="raise")
        if key.isna().any() or (~key.map(lambda x: float("-inf") < x < float("inf"))).any() or (key < 0).any() or key.sum() <= 0:
            raise ValueError(f"Missing positive GDP/facility weights for {country}/{sector}")
        total = industrial_production.at[country, sector]
        if pd.isna(total) or not float("-inf") < total < float("inf") or total < 0:
            raise ValueError(f"Invalid national industrial quantity for {country}/{sector}")
        nodal_production.loc[buses, sector] = total * key / key.sum()
    return nodal_production
'''

LOADER = '''def load_GDP(year=2015, update=False, out_logging=False,
             name_file_nc="GDP_PPP_1990_2015_5arcmin_v2.nc"):
    """Use only a raster derived from this raw NC and selected year.

    Old bundles can contain an unrelated regional TIFF with the global filename.
    Rebuild that cache from the existing source; do not download or update data.
    """
    import hashlib
    GDP_nc = os.path.join(BASE_DIR, "data", "GDP", name_file_nc)
    GDP_tif = GDP_nc[:-2] + "tif"
    with open(GDP_nc, "rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    with xr.open_dataset(GDP_nc) as source:
        years = source.time.values
        selected_year = float(year if year in years else years[-1])
        shape = (source.sizes["latitude"], source.sizes["longitude"])
    valid = False
    if os.path.exists(GDP_tif) and not update:
        with rasterio.open(GDP_tif) as raster:
            valid = (raster.shape == shape and raster.crs == rasterio.crs.CRS.from_epsg(4326)
                     and raster.tags().get("source_sha256") == digest
                     and raster.tags().get("source_year") == str(selected_year))
    if not valid:
        convert_GDP(name_file_nc, year, out_logging)
        with rasterio.open(GDP_tif, "r+") as raster:
            raster.update_tags(source_sha256=digest, source_year=str(selected_year))
    return GDP_tif, os.path.basename(GDP_tif)
'''

def allocator_tests(repo):
    f = extract(repo/'scripts/build_industry_demand.py', ['country_to_nodal'])['country_to_nodal']
    keys = pd.DataFrame({'country':['ID','ID','SG'], 'gdp':[2.,3.,5.], 'steel':[1.,3.,0.]}, index=['ID0','ID1','SG0'])
    prod = pd.DataFrame({'other':[10.,20.], 'steel':[4.,8.]},index=['ID','SG'])
    results = {}
    for label, k, p in [('country_conservation',keys,prod), ('index_permutation',keys.iloc[::-1],prod.iloc[::-1])]:
        got = f(p,k).groupby(k.country).sum().reindex(p.index)
        results[label] = bool(np.allclose(got,p))
    for label, k, p in [
        ('reject_nan',keys.assign(gdp=[np.nan,3.,5.]),prod),
        ('reject_negative',keys.assign(gdp=[-2.,3.,5.]),prod),
        ('reject_infinite',keys.assign(gdp=[np.inf,3.,5.]),prod),
        ('reject_zero_country',keys.assign(gdp=[2.,3.,0.]),prod),
        ('reject_missing_total',keys.assign(country=['ID','ID','TL']),prod),
        ('reject_missing_nodes',keys,prod.rename(index={'SG':'TL'})),
    ]:
        try: f(p,k); results[label] = False
        except (ValueError, KeyError): results[label] = True
    return results

def carbon_tests(repo):
    import pypsa
    sys.path.insert(0,str(repo/'scripts'))
    sys.modules.pop('_helpers',None)
    from _helpers import migrate_config, _deep_merge_dicts
    default=yaml.safe_load((repo/'config.default.yaml').read_text())
    asean=yaml.safe_load((repo/'configs/config.asean.yaml').read_text())
    paper=json.loads((HERE.parent/'00_source_provenance/effective_config/baseline-aims-3H_2025.json').read_text())
    addlimit=extract(repo/'scripts/prepare_network.py',['add_co2limit'])['add_co2limit']
    addbudget=extract(repo/'scripts/prepare_sector_network.py',['add_co2_budget'],{'add_co2limit':addlimit})['add_co2_budget']
    expected=[1e9,820e6,640e6,460e6,280e6,100e6]
    out={}
    for name, override in [('official_asean',asean),('paper_legacy',{'co2_budget':dict(paper['co2_budget'],year={int(k):v for k,v in paper['co2_budget']['year'].items()})})]:
        config=migrate_config(_deep_merge_dicts(default,override))
        values=[]
        for year in range(2025,2051,5):
            n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=2,freq='h'));n.snapshot_weightings[:]=4380.
            addbudget(n,config['co2'],year)
            values.append(float(n.global_constraints.at['CO2Limit','constant']))
        out[name]={'annual_tonnes':values,'pass':bool(np.allclose(values,expected))}
    return out

def main():
    # Application is deliberately one-shot on fresh, clean upstream worktrees.
    for folder in ['fix_industrial_gdp','fix_carbon_config']:
        repo=BASE/folder
        assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()=='a3616a68ee44592af6527ca9024a90f1956646ae', 'Use a fresh pinned worktree, or run the committed tests directly'
        assert not subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip(), 'Do not overwrite existing edits'
    result={}
    repo=BASE/'fix_industrial_gdp'
    result['allocator_before']=allocator_tests(repo)
    replace_function(repo/'scripts/build_industry_demand.py','country_to_nodal',ALLOCATOR)
    replace_function(repo/'scripts/build_shapes.py','load_GDP',LOADER)
    p=repo/'scripts/build_shapes.py';s=p.read_text();old='GDP_dataset.rio.to_raster(GDP_tif)'
    assert old in s
    p.write_text(s.replace(old,'GDP_dataset.rio.write_crs("EPSG:4326", inplace=True)\n    GDP_dataset.rio.to_raster(GDP_tif)',1))
    # Refuse upstream's implicit zero for an absent national industrial record.
    p=repo/'scripts/build_industry_demand.py';s=p.read_text()
    old='        # fill industry_base_totals\n'
    assert old in s
    s=s.replace(old,'        missing_countries = set(countries) - set(industry_base_totals.index.get_level_values(0))\n        if missing_countries:\n            raise ValueError(f"Missing national industrial data: {sorted(missing_countries)}; do not assume zero")\n\n'+old,1);p.write_text(s)
    result['allocator_after']=allocator_tests(repo)
    assert all(result['allocator_after'].values())
    # Store standalone regression harness with the fix so it can be reviewed/run.
    t=repo/'tests/test_industrial_conservation.py';t.parent.mkdir(exist_ok=True)
    t.write_text('''"""Regression: country totals, missingness and ordering (run as a script)."""\nimport ast\nfrom pathlib import Path\nfrom itertools import product\nimport pandas as pd\nimport numpy as np\n'''+__import__('inspect').getsource(extract).replace('dict(ENV, **(env or {}))','dict(pd=pd, product=product, **(env or {}))')+'\n'+__import__('inspect').getsource(allocator_tests)+'\nif __name__ == "__main__":\n    results=allocator_tests(Path(__file__).resolve().parents[1])\n    print(results)\n    assert all(results.values())\n')
    crepo=BASE/'fix_carbon_config'
    result['carbon_before']=carbon_tests(crepo)
    p=crepo/'configs/config.asean.yaml';s=p.read_text();assert s.count('co2base_value: 1.0e+09')==1
    p.write_text(s.replace('co2base_value: 1.0e+09 # choose from: [co2limit, co2base, absolute, {float}]','base_value: 1.0e+09 # absolute base in tCO2/year; scaled by year factors'))
    result['carbon_after']=carbon_tests(crepo)
    assert all(x['pass'] for x in result['carbon_after'].values())
    (HERE/'ENGINEERING_TEST_RESULTS.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
