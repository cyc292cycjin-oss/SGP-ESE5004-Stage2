"""Validate future-run schema behavior using clearly synthetic records."""
import copy, json, unittest
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
ROOT=Path(__file__).resolve().parents[2]
SCHEMA=json.loads((ROOT/'research/04_model_assembly/gate1/PHASE4_RUN_MANIFEST_SCHEMA.json').read_text())
VALIDATOR=Draft202012Validator(SCHEMA,format_checker=FormatChecker())
def fixture():
    x={k:'SCHEMA_TEST_ONLY' for k in SCHEMA['required']}
    for k in ['config','environment','spatial_resolution','temporal_resolution','carbon_policy','other_cross_border_carriers']:
        x[k]={'fixture':True}
    x.update(git_commit='a'*40,config_sha256='b'*64,input_manifest_sha256='c'*64,
             weather_year=2013,start_time='2026-10-04T00:00:00Z',end_time=None,objective=None,
             output_network=None,output_sha256=None,solver_status='NOT_RUN',cross_border_electricity_status='NOT_IMPLEMENTED')
    return x
class ManifestSchema(unittest.TestCase):
    def test_schema(self):Draft202012Validator.check_schema(SCHEMA)
    def test_not_run(self):VALIDATOR.validate(fixture())
    def test_each_required_field(self):
        for key in SCHEMA['required']:
            x=fixture();del x[key]
            with self.assertRaises(ValidationError,msg=key):VALIDATOR.validate(x)
    def test_false_result_rejected(self):
        x=fixture();x['objective']=42
        with self.assertRaises(ValidationError):VALIDATOR.validate(x)
    def test_malformed_hash(self):
        x=fixture();x['config_sha256']='short'
        with self.assertRaises(ValidationError):VALIDATOR.validate(x)
    def test_timestamp(self):
        x=fixture();x['start_time']='yesterday'
        with self.assertRaises(ValidationError):VALIDATOR.validate(x)
    def test_finished_requires_output(self):
        x=fixture();x['solver_status']='FINISHED'
        with self.assertRaises(ValidationError):VALIDATOR.validate(x)
        x.update(end_time='2026-10-04T01:00:00Z',output_network='SYNTHETIC_NOT_A_FILE.nc',output_sha256='d'*64)
        VALIDATOR.validate(x)
if __name__=='__main__':unittest.main(verbosity=2)
