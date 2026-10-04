"""A second isolated candidate: reject mismatched actual Load target nodes."""
from pathlib import Path
import shutil,subprocess
R=Path(__file__).resolve().parent
V=Path('/home/jin/research/SGP_ESE5004_Stage2/phase3b2/shipping_allocation_validation')
assert subprocess.check_output(['git','-C',str(V),'rev-parse','HEAD']).decode().strip()=='512c6cc2e53c579976d269486a7e328a0f372017'
assert subprocess.check_output(['git','-C',str(V),'branch','--show-current']).decode().strip()=='codex/transport-shipping-target-guard'
p=V/'scripts/prepare_sector_network.py'
text=p.read_text()
line='    navigation_mw = allocated.sum(axis=1, skipna=False) * 1e6 / 8760\n'
assert text.count(line)==1
text=text.replace(line,line+'''    load_nodes = pd.Index(spatial.nodes)
    if load_nodes.has_duplicates or set(load_nodes) != set(navigation_mw.index):
        raise ValueError("shipping allocation: load targets differ from allocated AC nodes")
    navigation_mw = navigation_mw.reindex(load_nodes)
''')
# Preserve the frozen upstream blob's line-ending style, not read_text's
# universal-newline normalization. This keeps the final base-to-tip diff small.
base=subprocess.check_output(['git','-C',str(V),'show','a3616a68ee44592af6527ca9024a90f1956646ae:scripts/prepare_sector_network.py'])
style='\r\n' if base.count(b'\r\n')==base.count(b'\n') else '\n'
p.write_bytes(text.replace('\n',style).encode('utf8'))
shutil.copyfile(R/'candidate/test_shipping_allocation.py', V/'tests/transport/test_shipping_allocation.py')
print('Applied exact target-node guard; preserved frozen source line endings.')
