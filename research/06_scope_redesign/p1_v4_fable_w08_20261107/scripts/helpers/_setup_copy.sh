set -u
WT=/home/jin/wt_v4_fable
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
T=/home/jin/v4fable
mkdir -p $T
echo "== sizes in worktree =="; du -sh $WT/research_inputs $WT/scripts_project $WT/configs $WT/tests 2>/dev/null
echo "== ignored inputs in main checkout =="
( cd $MAIN && git ls-files --others --ignored --exclude-standard research_inputs ) > $T/ignored_inputs.txt
wc -l $T/ignored_inputs.txt
( cd $MAIN && cat $T/ignored_inputs.txt | xargs -d '\n' du -ch 2>/dev/null | tail -1 )
echo "== tracked research_inputs missing from worktree (should be none) =="
( cd $WT && git ls-files research_inputs | while read f; do [ -e "$f" ] || echo "MISSING $f"; done | head )
echo "== copy tracked parts =="
mkdir -p $T/repo
rsync -a --exclude __pycache__ --exclude .pytest_cache $WT/scripts_project $WT/configs $WT/tests $WT/research_inputs $T/repo/
echo "== copy ignored inputs from main checkout (only if absent in copy) =="
( cd $MAIN && rsync -a --ignore-existing --files-from=$T/ignored_inputs.txt . $T/repo/ )
du -sh $T/repo
echo "== head of ignored list =="; head -30 $T/ignored_inputs.txt
echo "== git ignore check: is research_inputs/assembly_v1/sources tracked? =="
( cd $WT && git ls-files research_inputs/assembly_v1/sources | wc -l; ls research_inputs/assembly_v1/sources | head -40 )
