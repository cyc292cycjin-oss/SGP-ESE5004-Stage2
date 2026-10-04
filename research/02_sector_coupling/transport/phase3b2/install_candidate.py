"""Apply only the reviewed allocation patch in the isolated validation checkout."""
from pathlib import Path
import shutil
import subprocess

R = Path(__file__).resolve().parent
V = Path('/home/jin/research/SGP_ESE5004_Stage2/phase3b2/shipping_allocation_validation')
assert subprocess.check_output(['git','-C',str(V),'rev-parse','HEAD']).decode().strip() == 'a3616a68ee44592af6527ca9024a90f1956646ae'
assert subprocess.check_output(['git','-C',str(V),'branch','--show-current']).decode().strip() == 'codex/transport-shipping-allocation'
p = V/'scripts/prepare_sector_network.py'
text = p.read_text()
start = text.index('def add_shipping(')
end = text.index('\ndef ', start+1)
function = text[start:end]
function = function.replace('navigation_demand = energy_totals.loc[countries, all_navigation].sum(axis=1)', 'navigation_accounts = energy_totals.loc[countries, all_navigation]')
a = function.index('    ind = pd.DataFrame(n.buses.index[n.buses.carrier == "AC"])')
b = function.index('    if options["shipping_hydrogen_liquefaction"]:', a)
function = function[:a] + '''    allocated = allocate_shipping_demand(
        ports, navigation_accounts, n.buses.loc[n.buses.carrier == "AC"]
    )
    navigation_mw = allocated.sum(axis=1, skipna=False) * 1e6 / 8760
    ports = pd.DataFrame({"p_set": shipping_hydrogen_share * efficiency * navigation_mw})

''' + function[b:]
a = function.index('        ports["p_set"] = (', function.index('    if shipping_hydrogen_share < 1:'))
b = function.index('\n        n.madd(', a)
function = function[:a] + '        ports["p_set"] = shipping_oil_share * navigation_mw\n' + function[b:]
assert 'map(navigation_demand)' not in function
text = text[:start] + function + text[end:]
text = text.replace('import pandas as pd', 'import pandas as pd\nfrom _shipping_allocation import allocate_shipping_demand', 1)
assert text.count('from _shipping_allocation import') == 1
p.write_text(text)
shutil.copyfile(R/'candidate/_shipping_allocation.py', V/'scripts/_shipping_allocation.py')
d = V/'tests/transport'; d.mkdir(parents=True, exist_ok=True)
initial=R/'candidate/test_shipping_allocation_initial.py'
shutil.copyfile(initial if initial.exists() else R/'candidate/test_shipping_allocation.py', d/'test_shipping_allocation.py')
print('Patched isolated allocation candidate only; source energy, carbon and model configs unchanged.')
