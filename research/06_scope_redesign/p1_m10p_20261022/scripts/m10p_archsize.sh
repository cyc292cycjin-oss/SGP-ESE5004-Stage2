cd /home/jin/wt_m10p_20261022
echo "HEAD archive gz bytes: $(git archive --format=tar.gz HEAD | wc -c)"
echo "largest tracked dirs (tar bytes):"; for d in research results docs data scripts_project research_inputs configs tests cutouts resources; do [ -e $d ] && echo "$d $(git archive --format=tar HEAD $d 2>/dev/null | wc -c)"; done
