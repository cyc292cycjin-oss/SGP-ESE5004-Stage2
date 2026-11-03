# V3 screening (ON the instance, read-only): container start time (process 1) for the occupancy estimate of the cost line; the console stays authoritative.
echo "NOW $(TZ=Asia/Singapore date '+%F %T') SGT"
echo "PID1_START $(TZ=Asia/Singapore ps -o lstart= -p 1) SGT"
echo "PID1_ELAPSED_S $(ps -o etimes= -p 1 | tr -d ' ')"
