import importlib.util
import logging
import os
from pathlib import Path
import pyproj
os.environ['PROJ_DATA'] = pyproj.datadir.get_data_dir()
logging.disable(logging.WARNING)
import pandas as pd
import pypsa
from pypsa.clustering.spatial import get_clustering_from_busmap as original

spec = importlib.util.spec_from_file_location('candidate', Path(__file__).with_name('line_country_clustering.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fixed = module.get_clustering_from_busmap

def network():
    n = pypsa.Network()
    n.add('Bus', 'a', v_nom=110, x=106.0, y=11.0)
    n.add('Bus', 'b', v_nom=110, x=106.1, y=11.1)
    n.buses['country'] = pd.Series({'a': 'VN', 'b': 'KH'})
    for name, b0, b1, country in [('forward','a','b','VN'), ('reverse','b','a','KH')]:
        n.add('Line', name, bus0=b0, bus1=b1,
              r=0.1, x=0.3, s_nom=200, length=15)
    n.lines['country'] = pd.Series({'forward': 'VN', 'reverse': 'KH'})
    return n

n = network()
mapping = n.buses.index.to_series()
try:
    original(n, mapping)
except AssertionError as error:
    assert 'country' in str(error)
else:
    raise AssertionError('Original opposing-direction case should fail')
before = n.lines.copy(deep=True)
result = fixed(n, mapping).network
pd.testing.assert_frame_equal(n.lines, before)
assert len(result.lines) == 1
assert result.lines.country.eq(result.lines.bus0.map(result.buses.country)).all()
assert set(result.buses.country) == {'VN','KH'}
assert result.lines.s_nom.iloc[0] == 400
control = network()
control.lines = control.lines.drop(columns='country')
reference = original(control, mapping).network
pd.testing.assert_frame_equal(result.lines.drop(columns='country'), reference.lines)

# Also test cluster IDs that reverse the original ordering.
remap = pd.Series({'a':'z', 'b':'a'})
reordered = fixed(n, remap).network
assert reordered.lines.country.eq(reordered.lines.bus0.map(reordered.buses.country)).all()
assert reordered.lines.country.iloc[0] == 'KH'
pd.testing.assert_frame_equal(n.lines, before)

# Real conflicting pair, with its existing parameters and bus metadata.
p=Path('/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean')
real=pypsa.Network(p/'networks/baseline-aims-3H-tutorial/elec.nc')
pair=real.lines.loc[['1274599202-1_0','1274599211-1_0']].copy()
# The simplify_network workflow drops these descriptive columns before this call.
pair=pair.drop(columns=['symbol','tags','under_construction','onshore_bus','geometry',
                        'underground','project_status','substation_lv','substation_off'], errors='ignore')
small=pypsa.Network()
small.import_components_from_dataframe(real.buses.loc[['1098','2114']], 'Bus')
small.import_components_from_dataframe(pair, 'Line')
small.import_components_from_dataframe(real.line_types.loc[real.line_types.index.difference(small.line_types.index)], 'LineType')
before=small.lines.copy(deep=True)
out=fixed(small, small.buses.index.to_series(),
          line_strategies={'v_nom':'first','geometry':'first','bounds':'first'}).network
pd.testing.assert_frame_equal(small.lines,before)
assert out.lines.country.eq(out.lines.bus0.map(out.buses.country)).all()
print('PASS: original failure reproduced; opposite directions and reversed cluster IDs handled; input restored; all non-country aggregated line attributes identical to PyPSA control; real VN-KH pair passed.')
