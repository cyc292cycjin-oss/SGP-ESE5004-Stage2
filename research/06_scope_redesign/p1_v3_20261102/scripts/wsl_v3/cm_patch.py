p = "/home/jin/v3/commit.sh"
s = open(p).read()
a = 'git add -f "$D"\n'
b = 'git add -f "$D"\ngit add research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/run_dfx.sh research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/preflight_dfx.sh research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/preflight.sh research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/hpr_job.sh research/06_scope_redesign/p1_step4r_20261020/GATES_V6_NOTES.md\n'
assert s.count(a) == 1
open(p, "w").write(s.replace(a, b))
