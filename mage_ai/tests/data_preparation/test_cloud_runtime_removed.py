import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from mage_ai.data_preparation.logging.logger_manager_factory import LoggerManagerFactory
from mage_ai.data_preparation.shared.utils import get_template_vars, get_template_vars_no_db
from mage_ai.data_preparation.variable_manager import VariableManager
from mage_ai.io.config import EnvironmentVariableLoader
from mage_ai.orchestration.db.setup import get_postgres_connection_url


class RemovedCloudRuntimeTest(unittest.TestCase):
    def test_gcs_variables_fail_before_storage_initialization(self):
        with patch('mage_ai.data_preparation.variable_manager.LocalStorage') as storage:
            for create in [VariableManager, VariableManager.get_manager]:
                with self.assertRaisesRegex(ValueError, 'Unsupported storage scheme'):
                    create(repo_path='/tmp', variables_dir='unknown://private-bucket/results')
                with patch('mage_ai.data_preparation.variable_manager.get_variables_dir',
                           return_value='unknown://private-bucket/results'):
                    with self.assertRaisesRegex(ValueError, 'Unsupported storage scheme'):
                        create(repo_path='/tmp')
            storage.assert_not_called()

    def test_local_and_s3_variable_selection(self):
        manager = VariableManager.get_manager(repo_path='/tmp', variables_dir='/tmp/results')
        self.assertEqual(manager.variables_dir, '/tmp/results')
        with patch('mage_ai.data_preparation.variable_manager.S3VariableManager') as s3:
            self.assertIs(VariableManager.get_manager(variables_dir='s3://bucket/results'),
                          s3.return_value)
            s3.assert_called_once_with(repo_path=None, variables_dir='s3://bucket/results')

    def test_gcs_logging_does_not_fall_back_to_local(self):
        with patch('mage_ai.data_preparation.logging.logger_manager_factory.LoggerManager') as local:
            with self.assertRaisesRegex(ValueError, 'Unsupported logger type'):
                LoggerManagerFactory.get_logger_manager(
                    repo_config=SimpleNamespace(logging_config={'type': 'unknown'}))
            with patch(
                'mage_ai.data_preparation.logging.logger_manager_factory.get_repo_config',
                return_value=SimpleNamespace(logging_config={'type': 'unknown'}),
            ):
                with self.assertRaisesRegex(ValueError, 'Unsupported logger type'):
                    LoggerManagerFactory.get_logger_manager()
            local.assert_not_called()
            LoggerManagerFactory.get_logger_manager(
                repo_config=SimpleNamespace(logging_config={'type': 'file'}))
            local.assert_called_once()

    def test_s3_logger_selection(self):
        with patch('mage_ai.data_preparation.logging.s3_logger_manager.S3LoggerManager') as s3:
            self.assertIs(LoggerManagerFactory.get_logger_manager(
                repo_config=SimpleNamespace(logging_config={'type': 's3'})), s3.return_value)

    def test_template_helpers_only_register_supported_secrets(self):
        self.assertEqual(set(get_template_vars_no_db()), {'env_var', 'json_value'})

    def test_internal_secret_and_environment_helpers(self):
        secret = Mock(return_value='internal-value')
        with patch('mage_ai.data_preparation.shared.secrets.get_secret_value', secret):
            self.assertEqual(get_template_vars()['mage_secret_var']('internal'), 'internal-value')
        with patch.dict(os.environ, {'INTERNAL_TEST_VALUE': 'local-value'}):
            self.assertEqual(get_template_vars_no_db()['env_var']('INTERNAL_TEST_VALUE'), 'local-value')
            self.assertEqual(EnvironmentVariableLoader().get('INTERNAL_TEST_VALUE'), 'local-value')

    def test_azure_db_setting_fails_and_postgres_credentials_work(self):
        with patch.dict(os.environ, {
            'DB_USER': 'test', 'DB_PASS': 'test', 'DB_NAME': 'internal',
        }, clear=True):
            self.assertEqual(get_postgres_connection_url(),
                             'postgresql+psycopg2://test:test@127.0.0.1:5432/internal')

    def test_invalid_storage_is_not_persisted_or_created(self):
        import tempfile
        from pathlib import Path
        from mage_ai.data_preparation.repo_manager import RepoConfig
        from mage_ai.settings.repo import get_variables_dir
        with tempfile.TemporaryDirectory() as root:
            metadata = Path(root, 'metadata.yaml')
            metadata.write_text('spark_config: {}\n')
            config = RepoConfig(repo_path=root)
            before = metadata.read_text()
            with self.assertRaisesRegex(ValueError, 'Unsupported storage scheme'):
                config.save(variables_dir='unregistered://bucket/results')
            self.assertEqual(metadata.read_text(), before)
            with patch.dict(os.environ, MAGE_DATA_DIR='unregistered://bucket/results'), \
                    patch('os.makedirs') as create:
                with self.assertRaisesRegex(ValueError, 'Unsupported storage scheme'):
                    get_variables_dir(repo_path=root)
                create.assert_not_called()
