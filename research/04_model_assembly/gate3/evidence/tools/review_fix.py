from integrate import *
for rel in ['scripts_project/carrier_architecture.py','tests/research/test_carrier_carbon.py']:cp(rel)
command('gate3_validation',[P,'scripts_project/run_gate3_validation.py','--output',E])
command('gate3_config',[P,'scripts_project/check_research_carriers.py','--output',E/'RESEARCH_GATE3_CONFIG_CHECK.json'])
commits=json.loads((E/'IMPLEMENTATION_COMMITS.json').read_text())
commits.append(commit('fix: keep shared fuel prices independent of national availability\n\nSeparate common price provenance from country/node capacity and annual caps.\nValidation: synthetic equal-price unequal-availability imports stay isolated;\nall Gate3 tests and the unchanged Gate2 acceptance guard pass.', ['scripts_project/carrier_architecture.py','tests/research/test_carrier_carbon.py']))
(E/'IMPLEMENTATION_COMMITS.json').write_text(json.dumps(commits,indent=2))
print(git('rev-parse','HEAD'))
