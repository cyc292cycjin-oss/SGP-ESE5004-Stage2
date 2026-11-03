# V3 screening rerun (supplement 07) (ON the instance; instruction section 2 step 2): full checksum of the uploaded package, code unpacked exactly as the preflight does, COMMIT.
P=/root/autodl-tmp/v3_screen_dmax; cd $P || exit 2
echo "== files: $(find . -type f -not -path './repo/*' | wc -l); COMMIT $(cat COMMIT)"
[ "$(cut -c1-8 COMMIT)" = fbdf2c2e ] && echo "COMMIT matches fbdf2c2e" || { echo "COMMIT MISMATCH"; exit 2; }
sha256sum SHA256SUMS PACKAGE_MANIFEST.json | cut -c1-16,65-
sha256sum -c --quiet SHA256SUMS && echo "SHA256SUMS: all $(wc -l < SHA256SUMS) files OK" || { echo "CHECKSUM MISMATCH"; exit 2; }
C8=$(cut -c1-8 COMMIT)
if [ ! -d repo ]; then mkdir repo && tar xzf "code_${C8}.tar.gz" -C repo && cat COMMIT > repo/.package_commit && echo "code unpacked to ./repo: $(find repo -type f | wc -l) files, $(du -sh repo | cut -f1)"; else echo "./repo exists: commit $(cat repo/.package_commit)"; fi
df -h /root/autodl-tmp | tail -1
