"""V3 supplement 02: disk floor from the package definition."""
W = "/home/jin/wt_v3_20261102/"; P = W + "research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/preflight_dfx.sh"
s = open(P, encoding="utf-8", newline="").read()
a = '''NEED_CORES=${NEED_CORES:-17}; NEED_MEM_GIB=${NEED_MEM_GIB:-64}; NEED_DISK_GB=${NEED_DISK_GB:-45}; PAR_CORES=33'''
b = '''DEF_DISK=45; if [ -n "${BATCH_DEF:-}" ]; then DEF_DISK=$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1])).get('need_disk_gb', 45))" "$BATCH_DEF"); fi   # V3 supplement 02: the definition may raise the disk floor (five runs)
NEED_CORES=${NEED_CORES:-17}; NEED_MEM_GIB=${NEED_MEM_GIB:-64}; NEED_DISK_GB=${NEED_DISK_GB:-$DEF_DISK}; PAR_CORES=33'''
assert s.count(a) == 1; s = s.replace(a, b); open(P, "w", encoding="utf-8", newline="").write(s)
p = "/home/jin/v3/mk_def.py"; s = open(p, encoding="utf-8").read()
a = '''schedule=[["1", ["V1"], ["V2"]], ["2", ["V4"], ["V5"]], ["3", ["V3"], []]], time_limit_s=dict(V1=21600, V2=21600, V3=10800, V4=21600, V5=21600),'''
b = a + ''' need_disk_gb=90,'''
assert s.count(a) == 1; open(p, "w", encoding="utf-8").write(s.replace(a, b)); print("patched")
