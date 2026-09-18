import inspect
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mage_ai.usage_statistics.logger import UsageStatisticLogger


class Unreadable:
    def __getattribute__(self, name):
        raise AssertionError(f'Telemetry accessed application data: {name}')


class DisabledTelemetryTest(unittest.IsolatedAsyncioTestCase):
    async def test_all_compatibility_hooks_do_not_collect_or_send(self):
        def no_access(*args, **kwargs):
            raise AssertionError('Telemetry attempted network access or a database count')

        with patch('socket.socket.connect', no_access), patch('socket.getaddrinfo', no_access):
            logger = UsageStatisticLogger(project=Unreadable(), context_data=Unreadable())
            self.assertFalse(logger.help_improve_mage)
            for name, method in inspect.getmembers(logger, inspect.ismethod):
                if name.startswith('_'):
                    continue
                kwargs = {
                    key: no_access if key == 'count_func' else Unreadable()
                    for key, param in inspect.signature(method).parameters.items()
                    if param.default is inspect.Parameter.empty
                }
                value = method(**kwargs)
                if inspect.isawaitable(value):
                    value = await value
                self.assertEqual(value, {} if name == 'pipeline_run_ended_data' else False, name)

    async def test_legacy_opt_in_cannot_enable_collection(self):
        from mage_ai.data_preparation.repo_manager import RepoConfig
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'metadata.yaml').write_text('help_improve_mage: true\n')
            config = RepoConfig(repo_path=directory)
            self.assertFalse(config.help_improve_mage)
            self.assertFalse(config.to_dict()['help_improve_mage'])
            config.save(help_improve_mage=True)
            self.assertFalse(config.to_dict()['help_improve_mage'])
            self.assertFalse(RepoConfig(repo_path=directory).help_improve_mage)

    async def test_version_lookup_is_local(self):
        from mage_ai.api.resources.ProjectResource import get_latest_version
        from mage_ai.server.constants import VERSION
        with patch('socket.getaddrinfo', side_effect=AssertionError('Unexpected DNS lookup')):
            self.assertEqual(await get_latest_version(), VERSION)

    async def test_legacy_monitoring_environment_is_ignored(self):
        with patch.dict(os.environ, {'ENABLE_NEW_RELIC': 'True',
                                     'NEW_RELIC_CONFIG_PATH': '/missing/config'}):
            from mage_ai.services.newrelic import initialize_new_relic
            with patch('socket.getaddrinfo', side_effect=AssertionError('Unexpected DNS lookup')):
                self.assertEqual(initialize_new_relic(), (False, None))
