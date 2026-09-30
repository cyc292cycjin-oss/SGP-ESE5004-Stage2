"""Regression: country totals, missingness and ordering (run as a script)."""
import ast
from pathlib import Path
from itertools import product
import pandas as pd
import numpy as np
def extract(path, names, env=None):
    namespace = dict(pd=pd, product=product, **(env or {}))
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(nodes) == len(names), (path, names)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias('annotations')], level=0), *nodes], type_ignores=[])), str(path), 'exec'), namespace)
    return namespace

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

if __name__ == "__main__":
    results=allocator_tests(Path(__file__).resolve().parents[1])
    print(results)
    assert all(results.values())
