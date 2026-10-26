# DFX phase 4 (ON the instance): full checksum of the uploaded package; env_check of the EXISTING environment against the package's ENV_LOCK.txt
# (read-only use of the third-batch environment; result file written into the new package folder only).
P=/root/autodl-tmp/dfx_v8; cd $P || exit 2
echo "== files: $(find . -type f | wc -l); COMMIT $(cat COMMIT)"
sha256sum -c --quiet SHA256SUMS && echo "SHA256SUMS: all $(wc -l < SHA256SUMS) files OK" || echo "CHECKSUM MISMATCH"
E=/root/autodl-tmp/envs/pypsa-earth/bin/python
$E env/env_check.py env/ENV_LOCK.txt --out $P/ENV_CHECK_EXISTING.json; echo "env_check exit=$?"
$E - <<'P'
import json
r = json.load(open("/root/autodl-tmp/dfx_v8/ENV_CHECK_EXISTING.json"))
exact = r["key_all_equal"] and not r["only_lock"] and not r["only_instance"] and not r["version_differences"] and r["lock_packages"] == r["instance_packages"]
print("key_all_equal", r["key_all_equal"], "| packages", r["lock_packages"], r["instance_packages"], "| only_lock", len(r["only_lock"]), "only_instance", len(r["only_instance"]), "| version differences", len(r["version_differences"]), "| python", r["key_packages"]["python"])
print("ENV_EXACT_MATCH:", exact)
P
df -h /root/autodl-tmp | tail -1
