"""Add portable focused tests to each independent engineering fix branch."""
from engineering_review import *
import inspect

irepo=BASE/'fix_industrial_gdp'
crepo=BASE/'fix_carbon_config'
test='''"""Run with the project's existing Python environment; no network/downloads."""
from pathlib import Path
import ast, os, tempfile, logging
import numpy as np
import xarray as xr
import rasterio, rioxarray
'''
test+=inspect.getsource(extract).replace('dict(ENV, **(env or {}))','dict(xr=xr, os=os, rasterio=rasterio, logger=logging.getLogger(__name__), **(env or {}))')
test+='''
repo=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);d=root/'data/GDP';d.mkdir(parents=True)
    nc=d/'GDP_PPP_1990_2015_5arcmin_v2.nc'
    xr.Dataset({'GDP_PPP':(('time','latitude','longitude'),np.arange(8.).reshape(1,2,4))},coords={'time':[2015.], 'latitude':[45.,-45.], 'longitude':[-135.,-45.,45.,135.]}).to_netcdf(nc)
    # Wrong regional cache reproduces the failure independently of private inputs.
    xr.DataArray([[0.]],coords={'latitude':[0.],'longitude':[0.]},dims=['latitude','longitude']).rio.write_crs('EPSG:4326').rio.to_raster(str(nc)[:-2]+'tif')
    f=extract(repo/'scripts/build_shapes.py',['convert_GDP','load_GDP'],{'BASE_DIR':str(root)})
    path,_=f['load_GDP'](year=2020)
    with rasterio.open(path) as r:
        assert r.shape==(2,4) and r.crs.to_epsg()==4326
        assert r.tags()['source_year']=='2015.0'
        assert np.array_equal(r.read(1),np.arange(8.).reshape(2,4))
    stamp=Path(path).stat().st_mtime_ns
    f['load_GDP'](year=2020)
    assert Path(path).stat().st_mtime_ns==stamp, 'Valid cache should not be rewritten'
print('GDP coverage, source/year identity, values and cache reuse: PASS')
'''
(irepo/'tests/test_gdp_cache.py').write_text(test)
carbon='''"""ASEAN config and legacy paper config must yield identical annual budgets."""
from pathlib import Path
import ast, sys, logging
import pandas as pd
import numpy as np
import yaml
import pypsa
repo=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(repo/'scripts'))
from _helpers import migrate_config, _deep_merge_dicts
'''
carbon+=inspect.getsource(extract).replace('dict(ENV, **(env or {}))','dict(logger=logging.getLogger(__name__), **(env or {}))')
carbon+='''
default=yaml.safe_load((repo/'config.default.yaml').read_text())
asean=yaml.safe_load((repo/'configs/config.asean.yaml').read_text())
years=dict(zip(range(2025,2051,5),[1.,.82,.64,.46,.28,.1]))
legacy={'co2_budget':{'enable':True,'override_co2opt':True,'co2base_value':1.e9,'year':years}}
limit=extract(repo/'scripts/prepare_network.py',['add_co2limit'])['add_co2limit']
budget=extract(repo/'scripts/prepare_sector_network.py',['add_co2_budget'],{'add_co2limit':limit})['add_co2_budget']
for override in [asean,legacy]:
    config=migrate_config(_deep_merge_dicts(default,override))
    for hours in [8760.,144.]:
        for year,factor in years.items():
            n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=1,freq='h'));n.snapshot_weightings[:]=hours
            budget(n,config['co2'],year)
            assert np.isclose(n.global_constraints.at['CO2Limit','constant'],1e9*factor*hours/8760.)
assert not asean['co2']['budget']['enable'], 'Do not enable the budget in Baseline'
assert 'co2base_value' not in asean['co2']['budget'], 'Do not silently keep the mixed nested key'
print('Legacy/new trajectories, snapshot scaling and Baseline disable flag: PASS')
'''
(crepo/'tests').mkdir(exist_ok=True)
(crepo/'tests/test_asean_carbon_budget.py').write_text(carbon)
out={}
for repo,name in [(irepo,'test_industrial_conservation.py'),(irepo,'test_gdp_cache.py'),(crepo,'test_asean_carbon_budget.py')]:
    p=subprocess.run([sys.executable,str(repo/'tests'/name)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (HERE/'evidence'/name.replace('.py','.log')).write_text(p.stdout)
    out[name]={'returncode':p.returncode,'last_line':p.stdout.splitlines()[-1]};assert p.returncode==0,p.stdout
(HERE/'FIX_BRANCH_TESTS.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
