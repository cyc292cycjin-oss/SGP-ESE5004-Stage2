# V3 screening (ON the instance, read-only): install progress; the env_check result once it exists
P=/root/autodl-tmp/v3_screen; L=$P/ENV_INSTALL_CONSOLE.log
echo "== $(TZ=Asia/Singapore date '+%F %T') SGT"; [ -f "$L" ] && tail -n ${1:-14} "$L" | cut -c1-200
echo "== sizes: pkgs $(du -sh $P/conda_pkgs_cache 2>/dev/null | cut -f1) env $(du -sh /root/autodl-tmp/envs/pypsa-earth 2>/dev/null | cut -f1)"
J=$P/env/ENV_CHECK.json
if [ -f "$J" ]; then /root/autodl-tmp/envs/pypsa-earth/bin/python - "$J" <<'X'
import json, sys
r = json.load(open(sys.argv[1]))
exact = r["key_all_equal"] and not r["only_lock"] and not r["only_instance"] and not r["version_differences"] and r["lock_packages"] == r["instance_packages"]
print("key_all_equal", r["key_all_equal"], "| packages", r["lock_packages"], r["instance_packages"], "| only_lock", len(r["only_lock"]), "only_instance", len(r["only_instance"]), "| version differences", len(r["version_differences"]), "| python", r["key_packages"]["python"])
print("ENV_EXACT_MATCH:", exact)
X
fi
df -h /root/autodl-tmp | tail -1
