"""Check installed wheels, server/UI startup, and a local three-block pipeline.

Run inside the built image, with this file mounted at /tmp/mage-smoke.py.
No repository bind mount or external database is needed.
"""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import urllib.error
import urllib.request


def check_packages():
    for name in ('mage-ai', 'mage-integrations'):
        distribution = importlib.metadata.distribution(name)
        origin = json.loads(distribution.read_text('direct_url.json') or '{}')
        assert origin.get('url', '').startswith('file:'), (name, origin)
        assert origin['url'].endswith('.whl'), (name, origin)
        print(f'{name} {distribution.version}: {origin["url"]}', flush=True)

    distribution = importlib.metadata.distribution('mage-ai')
    for asset in (
        'mage_ai/server/frontend_dist/index.html',
        'mage_ai/server/frontend_dist_base_path_template/index.html',
        'mage_ai/data_preparation/templates/repo/metadata.yaml',
        'mage_ai/orchestration/db/alembic.ini',
    ):
        assert Path(distribution.locate_file(asset)).is_file(), asset


def create_pipeline(repo):
    blocks = [
        ('load', 'data_loader', 'data_loaders', '''
import pandas as pd
@data_loader
def load_data(**kwargs):
    return pd.DataFrame({'value': [1, 2, 3]})
'''),
        ('transform', 'transformer', 'transformers', '''
@transformer
def transform_data(data, **kwargs):
    return data.assign(value=data['value'] * 2)
'''),
        ('export', 'data_exporter', 'data_exporters', '''
import os
@data_exporter
def export_data(data, **kwargs):
    assert data['value'].tolist() == [2, 4, 6]
    data.to_json(os.environ['MAGE_SMOKE_OUTPUT'], orient='records')
'''),
    ]
    metadata = []
    for index, (uuid, block_type, directory, code) in enumerate(blocks):
        (repo / directory).mkdir(exist_ok=True)
        (repo / directory / f'{uuid}.py').write_text(code)
        metadata.append(dict(
            uuid=uuid,
            name=uuid,
            type=block_type,
            language='python',
            upstream_blocks=[blocks[index - 1][0]] if index else [],
            downstream_blocks=[blocks[index + 1][0]] if index < len(blocks) - 1 else [],
        ))
    pipeline = repo / 'pipelines' / 'local_build_smoke'
    pipeline.mkdir(parents=True)
    (pipeline / 'metadata.yaml').write_text(json.dumps(dict(
        name='Local build smoke', uuid='local_build_smoke', type='python', blocks=metadata,
    )))


def check_clickhouse_dialect():
    from clickhouse_sqlalchemy import Table, engines, types
    from sqlalchemy import Column, MetaData, create_engine
    from sqlalchemy.schema import CreateTable

    # Compile locally; this creates no connection to a ClickHouse server.
    engine = create_engine('clickhouse+http://localhost/default')
    table = Table('smoke', MetaData(), Column('value', types.Int32), engines.Memory())
    statement = str(CreateTable(table).compile(dialect=engine.dialect))
    assert 'Int32' in statement and 'Memory' in statement, statement
    engine.dispose()
    print('ClickHouse dialect with SQLAlchemy 2: PASS', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, help='Test mounted development sources')
    args = parser.parse_args()
    source_root = args.source_root.resolve() if args.source_root else None
    if source_root:
        assert (source_root / 'mage_ai').is_dir(), source_root
        assert (source_root / 'mage_integrations' / 'mage_integrations').is_dir(), source_root
    check_packages()
    check_clickhouse_dialect()
    with tempfile.TemporaryDirectory(prefix='mage-build-smoke-') as temporary:
        root = Path(temporary)
        repo = root / 'project'
        output = root / 'result.json'
        env = dict(os.environ)
        # These overrides affect only the disposable smoke-test instance.
        env.update(
            MAGE_DATA_DIR=str(root / 'data'),
            MAGE_DATABASE_CONNECTION_URL=f'sqlite:///{root / "orchestration.db"}',
            REQUIRE_USER_AUTHENTICATION='False',
            REQUIRE_USER_PERMISSIONS='False',
            SENTRY_DSN='',
            ENABLE_NEW_RELIC='',
            MAGE_SMOKE_OUTPUT=str(output),
            PYTHONPATH=f'{source_root}:{source_root / "mage_integrations"}' if source_root else '',
            INSTANCE_TYPE='server_and_scheduler',
        )
        if source_root and os.getenv('MAGE_OFFLINE_AUDIT') == '1':
            env['PYTHONPATH'] = f'{source_root / "scripts/offline_network_guard"}:' + env['PYTHONPATH']
        if source_root:
            subprocess.run(
                ['python', '-c',
                 'from pathlib import Path; import sys, mage_ai, mage_integrations; '
                 'root = Path(sys.argv[1]); '
                 'assert Path(mage_ai.__file__).is_relative_to(root / "mage_ai"); '
                 'assert Path(mage_integrations.__file__).is_relative_to('
                 'root / "mage_integrations"); '
                 'print("Mounted development imports: PASS")', str(source_root)],
                cwd=root, env=env, check=True, timeout=30,
            )
        subprocess.run(['mage', 'init', str(repo)], cwd=root, env=env, check=True, timeout=60)
        (repo / 'metadata.yaml').write_text(json.dumps(dict(
            project_type='standalone',
            variables_dir=str(root / 'variables'),
            help_improve_mage=os.getenv('MAGE_OFFLINE_AUDIT') == '1',
        )))
        create_pipeline(repo)
        log_path = root / 'server.log'
        with log_path.open('w') as log:
            server = subprocess.Popen(
                ['mage', 'start', str(repo), '--host', '127.0.0.1', '--port', '6789'],
                cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                deadline = time.monotonic() + 120
                while True:
                    if server.poll() is not None:
                        raise RuntimeError(f'Server exited: {server.returncode}')
                    try:
                        with urllib.request.urlopen(
                            'http://127.0.0.1:6789/api/statuses', timeout=2,
                        ) as response:
                            status = json.load(response)
                        assert 'statuses' in status, status
                        break
                    except (urllib.error.URLError, TimeoutError):
                        if time.monotonic() >= deadline:
                            raise RuntimeError('Server did not become ready within 120 seconds')
                        time.sleep(1)
                with urllib.request.urlopen('http://127.0.0.1:6789/', timeout=10) as response:
                    assert b'<html' in response.read().lower(), 'Missing frontend HTML'
                print('Server API and bundled frontend: PASS', flush=True)
                subprocess.run(
                    ['mage', 'run', str(repo), 'local_build_smoke'],
                    cwd=root, env=env, check=True, timeout=120,
                )
                assert json.loads(output.read_text()) == [
                    {'value': 2}, {'value': 4}, {'value': 6},
                ]
                print('Loader -> transformer -> exporter: PASS', flush=True)
            except BaseException:
                print(log_path.read_text(), flush=True)
                raise
            finally:
                try:
                    os.killpg(server.pid, signal.SIGTERM)
                    server.wait(timeout=15)
                except ProcessLookupError:
                    pass
                except subprocess.TimeoutExpired:
                    os.killpg(server.pid, signal.SIGKILL)
                    server.wait(timeout=5)


if __name__ == '__main__':
    main()
