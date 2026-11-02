from pathlib import Path
g = Path("/home/jin/v3/commit.sh"); s = g.read_text()
a = 'git add -A scripts_project configs tests "$D" 2>/dev/null\n'
assert a in s
s = s.replace(a, 'git add -A scripts_project configs tests 2>/dev/null\ngit add -f "$D"\ngit add -u research_inputs/registry_v5\n')
g.write_text(s)
