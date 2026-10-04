"""Recover existing GDP geometry and allocate ONLY observed 2019 quantities.

No growth, future conversion, ammonia substitution, imputation or optimisation.
Large regenerated geometry stays in the isolated fix worktree; JSON evidence is portable.
"""
from engineering_review import *
import atlite, geopandas as gpd
from rasterio.mask import mask
from types import SimpleNamespace

def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    repo=BASE/'fix_industrial_gdp'; source=OLD/'resources/baseline-aims-3H-tutorial'
    out=repo/'resources/phase2-industrial';out.mkdir(parents=True,exist_ok=True)
    raw=OLD/'data/GDP/GDP_PPP_1990_2015_5arcmin_v2.nc'
    cache=OLD/'data/GDP/GDP_PPP_1990_2015_5arcmin_v2.tif'
    dest=repo/'data/GDP';dest.mkdir(parents=True,exist_ok=True)
    for p in [raw,cache]:shutil.copy2(p,dest/p.name)
    hashes={str(p):sha(p) for p in [raw,cache]}
    funcs=extract(repo/'scripts/build_shapes.py',['load_GDP','convert_GDP'],{'BASE_DIR':str(repo)})
    with rasterio.open(dest/cache.name) as r:before={'shape':r.shape,'bounds':list(r.bounds),'crs':str(r.crs)}
    path,_=funcs['load_GDP'](year=2020)
    with rasterio.open(path) as r:
        after={'shape':r.shape,'bounds':list(r.bounds),'crs':str(r.crs),'tags':r.tags()}
        shapes=gpd.read_file(source/'shapes/gadm_shapes.geojson').set_index('GADM_ID')
        assert shapes.crs==r.crs
        shapes['gdp']=[float(np.nansum(mask(r,[g],all_touched=True,crop=True,nodata=0)[0])) for g in shapes.geometry]
    shapes.to_file(out/'gadm_shapes_with_gdp.geojson',driver='GeoJSON')
    cutout=atlite.Cutout(OLD/'cutouts/asean-2013-era5-tutorial.nc')
    I=atlite.cutout.compute_indicatormatrix(shapes.geometry,cutout.grid.geometry)
    gdp_grid=I.dot(shapes.gdp)
    regions_path=source/'bus_regions/regions_onshore_elec_s_50.geojson'
    regions=gpd.read_file(regions_path)
    clustered=cutout.indicatormatrix(regions.set_index('name').geometry.buffer(0)).dot(gdp_grid)
    gdp=pd.DataFrame({'total':clustered,'ct':regions.country.values},index=regions.name)
    gdp['fraction']=gdp.total/gdp.ct.map(gdp.groupby('ct').total.sum())
    assert np.isfinite(gdp.total).all() and (gdp.groupby('ct').total.sum()>0).all()
    gdp.to_csv(out/'gdp_clustered.csv')
    sys.path.insert(0,str(repo/'scripts'))
    from _helpers import locate_bus,read_csv_nafix
    countries=regions.country.unique().tolist()
    geomodule=extract(repo/'scripts/build_industrial_distribution_key.py',['build_nodal_distribution_key','match_technology'],{
      'read_csv_nafix':read_csv_nafix,'snakemake':SimpleNamespace(input=SimpleNamespace(
       clustered_gdp_layout=str(out/'gdp_clustered.csv'),clustered_pop_layout=str(source/'population_shares/pop_layout_elec_s_50_2030.csv')))})
    facilities=pd.read_csv(OLD/'resources/industrial_database.csv',keep_default_na=False)
    facilities=facilities[facilities.country.isin(countries)].copy();facilities.capacity=pd.to_numeric(facilities.capacity)
    facilities=geomodule['match_technology'](facilities)
    facilities=facilities[~facilities.quality.isin(['nonexistent','unavailable'])]
    mapped=locate_bus(facilities,countries,1,str(regions_path),False).set_index('gadm_1')
    keys=geomodule['build_nodal_distribution_key'](mapped,regions,mapped.industry.dropna().unique(),countries)
    keys.to_csv(out/'industrial_distribution_key.csv')
    basepath=source/'demand/base_industry_totals_2030.csv'
    national=pd.read_csv(basepath,index_col=[0,1])
    valid_countries=sorted(set(countries)&set(national.index.get_level_values(0)))
    missing_countries=sorted(set(countries)-set(valid_countries))
    allocator=extract(repo/'scripts/build_industry_demand.py',['country_to_nodal'])['country_to_nodal']
    factors=pd.DataFrame(1.,index=valid_countries,columns=national.columns)
    weights=allocator(factors,keys[keys.country.isin(valid_countries)])
    # Unobserved national sector/carrier cells are excluded, not silently set to zero.
    long=national.loc[valid_countries].stack().rename('national_MWh').reset_index()
    long.columns=['country','carrier','industry','national_MWh']
    records=[]
    conservation=[]
    for row in long.itertuples(index=False):
        w=weights.loc[keys.country==row.country,row.industry]
        vals=w*row.national_MWh
        err=float(vals.sum()-row.national_MWh)
        assert np.isclose(vals.sum(),row.national_MWh,rtol=1e-12,atol=1e-6)
        conservation.append({'country':row.country,'carrier':row.carrier,'industry':row.industry,'national_MWh':row.national_MWh,'node_sum_MWh':float(vals.sum()),'absolute_error_MWh':abs(err)})
        records.extend({'node':n,'country':row.country,'carrier':row.carrier,'industry':row.industry,'MWh':float(v)} for n,v in vals.items())
    node=pd.DataFrame(records)
    bycountry=[]
    for country in valid_countries:
        n=float(long.loc[long.country==country,'national_MWh'].sum());v=float(node.loc[node.country==country,'MWh'].sum())
        bycountry.append({'country':country,'national_MWh':n,'node_sum_MWh':v,'absolute_error_MWh':abs(v-n),'relative_error':abs(v-n)/n if n else 0.,'status':'OBSERVED_2019_QUANTITIES_ONLY'})
    bycountry.extend({'country':c,'national_MWh':None,'node_sum_MWh':None,'absolute_error_MWh':None,'relative_error':None,'status':'MISSING_NOT_ZERO'} for c in missing_countries)
    evidence={'raw_source_unchanged':all(sha(p)==h for p,h in hashes.items()),'raw_hashes':hashes,
      'national_source_sha256':sha(basepath),'raster_before':before,'raster_after':after,
      'raster_sha256':sha(path),'gdp_by_country':gdp.groupby('ct').total.sum().to_dict(),
      'geography':'existing tutorial 48 nodes / 50 requested clusters; no formal network run',
      'GDP_year_requested':2020,'GDP_year_available_used':2015,'growth_applied':False,
      'observed_cells':len(long),'missing_national_cells':int(national.loc[valid_countries].isna().sum().sum()),
      'mapped_facilities':len(mapped),'countries':bycountry,'country_carrier_industry_checks':conservation,
      'max_cell_absolute_error_MWh':max(x['absolute_error_MWh'] for x in conservation),
      'large_derived_directory':str(out)}
    assert evidence['raw_source_unchanged']
    (HERE/'INDUSTRIAL_RECOVERY_EVIDENCE.json').write_text(json.dumps(evidence,indent=2))
    (HERE/'INDUSTRIAL_NODE_OBSERVED.json').write_text(json.dumps(records,indent=2))
    print(json.dumps({k:v for k,v in evidence.items() if k not in ['country_carrier_industry_checks']},indent=2))
if __name__=='__main__':main()
