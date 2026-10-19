# S4N licence location check (runs ON the instance via "ssh bash -s"; read-only). The licence content is never printed: copies are found by name,
# by size (same byte count) and by comparing SHA256 values inside this script (the hash itself is not printed).
L=/root/.gurobi/gurobi.lic
echo "== licence file"
stat -c "path %n | mode %a | owner %U:%G | size %s bytes | mtime %y" $L 2>&1
stat -c "dir %n | mode %a | owner %U" /root/.gurobi
echo "dir entries: $(ls -A /root/.gurobi | wc -l) ($(ls -A /root/.gurobi | tr '\n' ' '))"
SZ=$(stat -c %s $L); H=$(sha256sum $L | cut -d' ' -f1)
echo "== files named *.lic / gurobi* licence-like names (excluding the licence itself and package code)"
find / -xdev \( -iname "*.lic" -o -iname "gurobi.lic*" -o -iname "*grb*lic*" \) -type f 2>/dev/null | grep -v "^$L$"
find /root/autodl-tmp /tmp /dev/shm \( -iname "*.lic" -o -iname "gurobi.lic*" \) -type f 2>/dev/null
echo "(end of name search)"
echo "== files of the same size ($SZ bytes) with the same SHA256 (copies), searched in / (root fs), /root/autodl-tmp, /tmp, /dev/shm"
n=0; c=0
for f in $( { find / -xdev -type f -size ${SZ}c 2>/dev/null; find /root/autodl-tmp /tmp /dev/shm -type f -size ${SZ}c 2>/dev/null; } | sort -u ); do
  n=$((n+1)); [ "$f" = "$L" ] && continue
  if [ "$(sha256sum "$f" 2>/dev/null | cut -d' ' -f1)" = "$H" ]; then c=$((c+1)); echo "COPY FOUND: $f"; fi
done
echo "same-size files checked: $n (incl. the licence itself); copies other than $L: $c"
echo "== rsync / scp residue (hidden temp files) in the data disk and /tmp"
find /root/autodl-tmp /tmp /root/.gurobi -name ".*" -type f 2>/dev/null | grep -v "/\.ipynb_checkpoints/" | head -20
echo "(end of residue list)"
echo "== licence keyword markers (names only, case-insensitive: licens[e]id / wlsacces[s]id / wlssecre[t]) in text files of the deployment folder, /tmp and /root/autodl-tmp"
grep -rIilE "licens[e]id|wlsacces[s]id|wlssecre[t]" /root/autodl-tmp /tmp 2>/dev/null | grep -v "^/root/autodl-tmp/s4m_cloud/repo/" | head -20
echo "(end of marker list; the unpacked code snapshot repo/ is listed separately:)"
grep -rIilE "wlsacces[s]id|wlssecre[t]" /root/autodl-tmp/s4m_cloud/repo 2>/dev/null | head -10
echo "== GRB_LICENSE_FILE in the environment of this shell: ${GRB_LICENSE_FILE:-unset}"
echo "== done"
