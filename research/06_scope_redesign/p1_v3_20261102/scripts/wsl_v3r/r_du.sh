# V3 screening rerun (supplement 07) (ON the instance, read-only): bytes received so far in the package folder (upload progress), rsync partial files
echo "$(TZ=Asia/Singapore date '+%T') SGT bytes $(du -sb /root/autodl-tmp/v3_screen_dmax 2>/dev/null | cut -f1) files $(find /root/autodl-tmp/v3_screen_dmax -type f 2>/dev/null | wc -l)"
find /root/autodl-tmp/v3_screen_dmax -name '.*' -type f -printf '%s %f\n' 2>/dev/null | head -3
