# DFX phase 4 (ON the instance, RUN_PLAN_DFX section 7 step 8): delete ONLY /root/.gurobi/gurobi.lic (never read or printed) after the results are
# recovered and verified; other licence-like names are listed (names only) and not touched. Refused while a runner / solve / analysis process runs.
L=/root/.gurobi/gurobi.lic
echo "== LIC_DELETE_TIME: $(TZ=Asia/Singapore date "+%F %T") SGT"
if ps -eo args | grep -E "[r]un_dfx|[s]2_solve|[g]urobi_cl|[l]23_violation|[s]4o_c1|[m]12_allocation|[m]12_rhs_audit|[g]ates_v6|[p]reflight_dfx"; then echo "REFUSED: process still running"; exit 2; fi
echo "/root/.gurobi: $([ -d /root/.gurobi ] && echo "directory, $(ls -A /root/.gurobi | wc -l) entries" || echo "no directory")"
if [ -e "$L" ]; then
  echo "LICENCE_PRESENT: $L ($(stat -c '%A %s B' "$L"))"
  shred -u "$L" 2>/dev/null || rm -f "$L"
  [ -e "$L" ] && echo "STILL PRESENT - delete failed" || echo "DELETED: $L at $(TZ=Asia/Singapore date "+%F %T") SGT"
else
  echo "LICENCE_ABSENT: $L (nothing to delete)"
fi
[ -e "$L" ] && echo "FINAL: present" || echo "FINAL: VERIFIED_ABSENT $L"
ls -la /root/.gurobi 2>&1
echo "== other licence-like file names (names only; conda package trees excluded):"
find /root/autodl-tmp /tmp /dev/shm /root/.gurobi \( -iname "gurobi.lic*" -o -iname "*.lic" \) -type f 2>/dev/null | grep -vE "^/root/autodl-tmp/envs/|/conda_pkgs_cache/"
echo "(end)"
