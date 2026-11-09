import pandas as pd
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
w = pd.read_csv('/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109/cache/CO2_ACCOUNT_ALL_WIDE.csv', keep_default_na=False)
w['F1'] = w.F1.astype(float); w['F2'] = w.F2.astype(float)
x = w[(w.section.isin(['pipeline', 'CO2 ship', 'CO2 transit ship', 'sink', 'CO2 export extra-ASEAN'])) & ((w.F1.abs() > 1e3) | (w.F2.abs() > 1e3))]
print(x.to_string())
d = w[(w.section == 'dual') & (w.item.str.startswith('total cap') | w.item.str.startswith('co2 stored node'))]
print(d.to_string())
s = w[w.section.isin(['source', 'use'])].groupby(['country']).agg(F1=('F1', 'sum'), F2=('F2', 'sum'))
print(s)
