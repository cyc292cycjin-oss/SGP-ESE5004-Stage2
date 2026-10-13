"""Local only: persistent truncated (T snapshots) D-1 run for rehearsing D-2/D-3 code paths. Same harness as D1 test T06.
Usage: python make_local_truncated_d1.py <release_d1> <frozen network> <run dir> <T>
"""
import sys, time, threading, logging
from pathlib import Path
REL, NET, RUN = map(Path, sys.argv[1:4]); T = int(sys.argv[4])
sys.path.insert(0, str(REL)); sys.path.insert(0, str(REL / 'helpers')); logging.disable(logging.WARNING)
import d1_build, d1_worker, d1_model, fixed_accounts
from c02_common import write, sha, read
RUN.mkdir(parents=True, exist_ok=False); now = time.time()
write(RUN / 'AUTHORIZATION.json', {'run_id': 'd1_build2920_LOCAL_TRUNCATED', 'source_network': str(NET), 'source_network_sha256': sha(NET), 'test_snapshots': T,
                                   'build_phase_seconds': 7200, 'build_absolute_deadline_epoch': now + 7200})
stop = threading.Event()
def hb():
    while not stop.is_set(): write(RUN / 'GUARD_HEARTBEAT.json', {'epoch': time.time()}); time.sleep(1)
threading.Thread(target=hb, daemon=True).start(); time.sleep(1.2)
d1_build.resources = lambda p: {}; d1_build.resource_gate = lambda r, start=False: None
real = d1_model.assemble_2920
def truncated(source, root, out, progress):
    n = real(source, root, out, progress)
    n.set_snapshots(n.snapshots[:T]); n.snapshot_weightings.loc[:, ['objective', 'generators', 'stores']] = 3.
    fixed_accounts.validate_exported_accounting = lambda m: None
    return n
d1_model.assemble_2920 = truncated
d1_build.main(RUN)
from d1_bridge import bridge
bridge(RUN / 'artifacts', RUN / 'bridge', lambda s: None)
g = d1_worker.build_gates(RUN, lambda s: None); d1_worker.artifact_index(RUN, lambda s: None)
stop.set(); print(g['status'], g['dimensions'])
