"""Run with the project's existing Python environment; no network/downloads."""
from pathlib import Path
import ast, os, tempfile, logging
import numpy as np
import xarray as xr
import rasterio, rioxarray
def extract(path, names, env=None):
    namespace = dict(xr=xr, os=os, rasterio=rasterio, logger=logging.getLogger(__name__), **(env or {}))
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(nodes) == len(names), (path, names)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias('annotations')], level=0), *nodes], type_ignores=[])), str(path), 'exec'), namespace)
    return namespace

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
