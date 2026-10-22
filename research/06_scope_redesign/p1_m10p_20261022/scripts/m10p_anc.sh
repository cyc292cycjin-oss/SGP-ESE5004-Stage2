cd /home/jin/wt_m12_20261021
H=1f46517d
for b in 820c2cae b018670c 168bff80 1f46517d 22f53c84 30d281b8 cefab870 69b67a97 0b681881 46135c52; do
  if git merge-base --is-ancestor $b $H; then echo "$b in"; else echo "$b MISSING"; fi
done
echo "--- FIXED_RUNS grep"
git grep -n "FIXED_RUNS" $H -- . | head -20
echo "--- s4q branch FIXED_RUNS"
git grep -n "FIXED_RUNS" 22f53c84 -- . | head -20
