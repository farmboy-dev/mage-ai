"""Create a disposable UI test project; run only in the isolated test container."""
import json
import os
import runpy
import subprocess
from pathlib import Path
assert os.getenv('MAGE_OFFLINE_AUDIT') == '1', 'Requires the offline audit test environment'
repo=Path('/tmp/offline-project')
Path('/tmp/outbound.jsonl').unlink(missing_ok=True)
if not repo.exists():
    subprocess.run(['mage','init',str(repo)],check=True)
(repo/'metadata.yaml').write_text(json.dumps({'project_type':'standalone','help_improve_mage':True,'features':{'add_new_block_v2':True,'compute_management':True},'emr_config':{'master_instance_type':'legacy'},'spark_config':{'spark_master':'local','app_name':'offline-ui'}}))
if not (repo / 'pipelines/local_build_smoke').exists():
    runpy.run_path('/workspace/scripts/smoke_test_local_build.py')['create_pipeline'](repo)
os.execvp('python',['python','/workspace/mage_ai/server/server.py','--host','0.0.0.0','--port','6789','--project',str(repo),'--manage-instance','0'])
