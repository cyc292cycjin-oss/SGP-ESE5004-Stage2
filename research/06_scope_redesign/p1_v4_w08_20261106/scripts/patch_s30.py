"""W08: redirect the per-mode outputs of s3_0_industry.py to DEMAND_OUT and stop after the per-mode tables in --only-mode (asserted edits)."""
from pathlib import Path

p = Path("/home/jin/wt_v4_w08/scripts_project/s3_0_industry.py")
s = p.read_text()
lines = s.split("\n")
n = 0
for i, ln in enumerate(lines):
    if (ln.startswith("        write_csv(") and 'DEMAND_DIR / f"INDUSTRY_2050_' in ln) or ln.startswith('    write_csv(gaps, DEMAND_DIR /') or ln.startswith('    write_csv(other_rows, DEMAND_DIR /'):
        lines[i] = ln.replace("DEMAND_DIR /", "DEMAND_OUT /", 1); n += 1
assert n == 11, n   # 9 per-mode tables + gaps + other bucket
s = "\n".join(lines)
old = '    write_csv(other_rows, DEMAND_OUT / "INDUSTRY_2050_OTHER_BUCKET.csv", list(other_rows[0].keys()))\n'
assert s.count(old) == 1
s = s.replace(old, old + '    if a.only_mode is not None:   # V4 W08: one mode only -> no cross-mode comparison tables, no registry fragment, no evidence file\n'
                          '        write_json(dict(script=SCRIPT, v4_w08_only_mode=a.only_mode, sources=dict(industry_cache=cache_sha, ats_table=sha256(a.ats_table) if a.ats_table else "",\n'
                          '                        output_rule=sha256(rule_tables[a.only_mode]) if a.only_mode in rule_tables else "", edgar=ed_sha), edgar_2a1_zero=a.edgar_2a1_zero,\n'
                          '                        cement_el_t19=cem_el_t19, biomass_cap_share=a.biomass_cap_share, gaps=len(gaps)), DEMAND_OUT / "INDUSTRY_2050_EVIDENCE.json")\n'
                          '        return\n')
p.write_text(s)
print("patched", n)
