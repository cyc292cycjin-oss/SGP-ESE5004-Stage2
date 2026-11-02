import re
t = open("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/tests/full.txt", errors="replace").read()
i = t.find("=== FAILURES"); sec = t[i:]
lines = [l for l in sec.splitlines() if re.match(r"^(/home|E  )", l)]
for l in lines:
    if not re.search(r"START:|CALLS\.txt|/out/|xit=0:fake", l):
        print(l[:260])
