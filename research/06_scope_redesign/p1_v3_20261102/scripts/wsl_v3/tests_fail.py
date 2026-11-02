import re
t = open("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/tests/full.txt", errors="replace").read()
print(len(t))
i = t.find("=== FAILURES")
print(t[:200])
sec = t[i:]
j = sec.find("warnings summary")
print(sec[:j if j > 0 else 9000][:9000])
for m in re.findall(r"^FAILED .*$", t, re.M)[:12]:
    print(m[:200])
