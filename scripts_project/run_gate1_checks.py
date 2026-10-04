"""Re-run integrated engineering and static regressions without any solver."""
import argparse, json, os, subprocess, sys, hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
root=Path(__file__).resolve().parents[1];out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
commands=[]
for name in ['test_gdp_cache.py','test_industrial_conservation.py','test_asean_carbon_budget.py']:
    commands.append((name,[sys.executable,str(root/'tests'/name)]))
for fix in ['E1','E2','E4']:
    commands.append((fix,[sys.executable,str(root/f'research/02_sector_coupling/buildings_engineering_tests/check_{fix}.py'),
                         '--repo',str(root),'--fix',fix,'--output',str(out/(fix+'.json'))]))
commands.append(('buildings_combined',[sys.executable,str(root/'tests/research/approved_buildings_regressions.py'),
                                     '--repo',str(root),'--fix','combined','--output',str(out/'buildings_combined.json')]))
commands.append(('static_framework',[sys.executable,str(root/'tests/research/test_phase4_static.py')]))
commands.append(('run_manifest_schema',[sys.executable,str(root/'tests/research/test_run_manifest_schema.py')]))
rows=[]
for name,cmd in commands:
    result=subprocess.run(cmd,cwd=root,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/(name+'.log')).write_bytes(result.stdout)
    rows.append(dict(test=name,returncode=result.returncode,status='PASS' if result.returncode==0 else 'FAIL',command=cmd))
tested_files=[root/'scripts_project/phase4_static.py',root/'scripts_project/run_gate1_checks.py',root/'research/04_model_assembly/gate1/PHASE4_RUN_MANIFEST_SCHEMA.json']
tested_files += [Path(cmd[1]) for _,cmd in commands]
tested_files += list((root/'configs/research').glob('*'))
tested_files += [root/'scripts'/name for name in ['build_industry_demand.py','build_shapes.py','prepare_sector_network.py','prepare_heat_data.py','final_asean_adjustment.py']]
report=dict(tests=rows,all_pass=all(r['status']=='PASS' for r in rows),solver_status='NOT_RUN',
            tested_file_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tested_files},
            git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip())
(out/'RUNNER_REPORT.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2));sys.exit(0 if report['all_pass'] else 1)
