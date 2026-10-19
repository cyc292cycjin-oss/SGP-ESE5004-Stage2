# S4N licence check, part 2 (runs ON the instance via "ssh bash -s"; read-only; prints names and counts only, never file content)
echo "== hidden temp files outside the unpacked code snapshot (rsync / scp residue)"
find /root/autodl-tmp /tmp /root/.gurobi -name ".*" -type f 2>/dev/null | grep -v "^/root/autodl-tmp/s4m_cloud/repo/" | grep -v "/tmp/tmux-" ; echo "(end)"
echo "== the two gurobi.lic files inside the conda installation: size / mtime / owning package (content not read)"
stat -c "%n | %s bytes | %y" /root/miniconda3/envs/pypsa-earth/lib/gurobi.lic /root/miniconda3/pkgs/gurobi-12.0.3-py311_0/lib/gurobi.lic 2>&1
grep -l "lib/gurobi.lic" /root/miniconda3/envs/pypsa-earth/conda-meta/*.json 2>/dev/null | xargs -r -n1 basename
echo "== repo/ files with licence keyword names: count of keyword occurrences followed by a UUID-like value (WLS ids and secrets are UUIDs)"
for f in $(grep -rIilE "wlsacces[s]id|wlssecre[t]" /root/autodl-tmp/s4m_cloud/repo 2>/dev/null); do
  k=$(grep -ciE "wlsacces[s]id|wlssecre[t]" "$f"); u=$(grep -ciE "(wlsacces[s]id|wlssecre[t])[^0-9a-z]{1,12}[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}" "$f")
  echo "${f#/root/autodl-tmp/s4m_cloud/repo/} | keyword lines $k | keyword followed by UUID-like value: $u"
done
echo "== done"
