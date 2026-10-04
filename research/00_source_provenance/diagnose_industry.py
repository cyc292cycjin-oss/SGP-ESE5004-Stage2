"""Read existing intermediate values; diagnose missingness without replacing data."""
from pathlib import Path
import ast, hashlib, json, sys
import numpy as np, pandas as pd, xarray as xr
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean')
D=REPO/'resources/baseline-aims-3H-tutorial'
def stats(a):
    a=np.asarray(a,dtype=float);f=a[np.isfinite(a)]
    return {'shape':list(a.shape),'finite':int(np.isfinite(a).sum()),'nan':int(np.isnan(a).sum()),'nonzero_finite':int(np.count_nonzero(f)),'sum_finite':float(f.sum()),'min':float(f.min()) if len(f) else None,'max':float(f.max()) if len(f) else None}
def main():
    out={};countries=['BN','KH','ID','LA','MY','MM','PH','SG','TH','TL','VN']
    for year in [2030,2040,2050]:
        base=pd.read_csv(D/f'demand/base_industry_totals_{year}.csv',index_col=[0,1]);base=base[base.index.get_level_values(0).isin(countries)]
        keys=pd.read_csv(D/f'demand/industrial_distribution_key_elec_s_50_{year}.csv',index_col=0)
        gdp=pd.read_csv(D/f'gdp_shares/gdp_layout_elec_s_50_{year}.csv',index_col=0)
        gdpx=xr.open_dataarray(D/f'gdp_shares/gdp_layout_{year}.nc')
        cagr=pd.read_csv(REPO/'data/demand/industry_growth_cagr.csv',index_col=0)
        for c in countries:
            if c not in cagr.index:cagr.loc[c]=cagr.loc['DEFAULT']
        production=(1+cagr.loc[countries])**(year-2019)
        # Execute only the pure mapping function extracted verbatim from current script.
        tree=ast.parse((REPO/'scripts/build_industry_demand.py').read_text())
        f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='country_to_nodal')
        from itertools import product
        env={'pd':pd,'product':product};exec(compile(ast.Module(body=[f],type_ignores=[]),'source_mapping','exec'),env)
        nodal=env['country_to_nodal'](production,keys)
        final=pd.read_csv(D/f'demand/industrial_energy_demand_per_node_elec_s_50_{year}.csv',index_col=0)
        out[str(year)]={'base_asean':stats(base),'base_electricity_MWh_by_country':base.xs('electricity',level=1).sum(axis=1).to_dict(),'base_missing_countries':sorted(set(countries)-set(base.index.get_level_values(0))),'key_gdp':stats(keys.gdp),'gdp_cluster':stats(gdp.total),'gdp_grid':stats(gdpx),'gdp_grid_attrs':gdpx.attrs,'nodal_growth_nan_by_column':nodal.isna().sum().to_dict(),'all_rows_have_nan_in_dot_input':bool(nodal.isna().any(axis=1).all()),'final':stats(final)}
        for source in [D/f'gdp_shares/gdp_layout_elec_s_50_{year}.csv']:
            dest=ROOT/'diagnostic_inputs'/source.name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(source.read_bytes())
    shapes=json.loads((D/'shapes/gadm_shapes.geojson').read_text())
    props=pd.DataFrame([f['properties'] for f in shapes['features']])
    out['gadm']={'rows':len(props),'columns':list(props.columns),'gdp':stats(props.gdp),'by_country':props.groupby('country').gdp.agg(['sum','count','min','max']).to_dict('index')}
    import rasterio
    tif=REPO/'data/GDP/GDP_PPP_1990_2015_5arcmin_v2.tif'
    with rasterio.open(tif) as r:
        out['gdp_raster']={'crs':str(r.crs),'bounds':list(r.bounds),'shape':list(r.shape),'count':r.count,'nodata':r.nodata,'tags':r.tags()}
        window=rasterio.windows.from_bounds(90,-12,142,30,r.transform)
        out['gdp_raster']['asean_rectangle']=stats(r.read(1,window=window,masked=True).filled(np.nan))
    nc=REPO/'data/GDP/GDP_PPP_1990_2015_5arcmin_v2.nc'
    with xr.open_dataset(nc) as ds:
        out['gdp_raw_nc']={'attrs':ds.attrs,'sizes':dict(ds.sizes),'coords':{k:{'first':str(ds[k].values.flat[0]),'last':str(ds[k].values.flat[-1])} for k in ds.coords},'variables':{k:ds[k].attrs for k in ds.data_vars}}
    # Snapshot metadata on already downloaded UNSD files, without another download.
    out['unsd_files']=[{'name':p.name,'bytes':p.stat().st_size} for p in sorted((REPO/'data/demand/unsd/data').glob('*.txt'))]
    (ROOT/'INDUSTRY_DIAGNOSTIC.json').write_text(json.dumps(out,indent=2,default=str))
    print(json.dumps(out,indent=2,default=str)[:14000])
if __name__=='__main__':main()
