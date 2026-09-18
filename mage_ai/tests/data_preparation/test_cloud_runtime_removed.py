import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from mage_ai.data_preparation.logging.logger_manager_factory import LoggerManagerFactory
from mage_ai.data_preparation.shared.utils import get_template_vars, get_template_vars_no_db
from mage_ai.data_preparation.variable_manager import VariableManager
from mage_ai.io.config import AWSSecretLoader, EnvironmentVariableLoader
from mage_ai.orchestration.db.setup import get_postgres_connection_url


class RemovedCloudRuntimeTest(unittest.TestCase):
    def test_gcs_variables_fail_before_storage_initialization(self):
        with patch('mage_ai.data_preparation.variable_manager.LocalStorage') as storage:
            for create in [VariableManager, VariableManager.get_manager]:
                with self.assertRaisesRegex(ValueError, 'GCS variable storage has been removed'):
                    create(repo_path='/tmp', variables_dir='gs://private-bucket/results')
                with patch('mage_ai.data_preparation.variable_manager.get_variables_dir',
                           return_value='gs://private-bucket/results'):
                    with self.assertRaisesRegex(ValueError, 'GCS variable storage has been removed'):
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
            with self.assertRaisesRegex(ValueError, 'GCS logging has been removed'):
                LoggerManagerFactory.get_logger_manager(
                    repo_config=SimpleNamespace(logging_config={'type': 'gcs'}))
            with patch(
                'mage_ai.data_preparation.logging.logger_manager_factory.get_repo_config',
                return_value=SimpleNamespace(logging_config={'type': 'gcs'}),
            ):
                with self.assertRaisesRegex(ValueError, 'GCS logging has been removed'):
                    LoggerManagerFactory.get_logger_manager()
            local.assert_not_called()
            LoggerManagerFactory.get_logger_manager(
                repo_config=SimpleNamespace(logging_config={'type': 'file'}))
            local.assert_called_once()

    def test_s3_logger_selection(self):
        with patch('mage_ai.data_preparation.logging.s3_logger_manager.S3LoggerManager') as s3:
            self.assertIs(LoggerManagerFactory.get_logger_manager(
                repo_config=SimpleNamespace(logging_config={'type': 's3'})), s3.return_value)

    def test_cloud_secret_loaders_fail_without_sdk_imports(self):
        original_import = __import__

        def checked_import(name, *args, **kwargs):
            if name.split('.')[0] in {'azure', 'boto3', 'botocore'}:
                self.fail(f'Unexpected cloud SDK import: {name}')
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=checked_import):
            variables = get_template_vars_no_db()
            with self.assertRaisesRegex(ValueError, 'Azure Key Vault has been removed') as azure:
                variables['azure_secret_var']('private-secret-name')
            with self.assertRaisesRegex(ValueError, 'AWSSecretLoader has been removed') as aws:
                AWSSecretLoader(aws_secret_access_key='private-key')
            self.assertNotIn('private-secret-name', str(azure.exception))
            self.assertNotIn('private-key', str(aws.exception))

    def test_internal_secret_and_environment_helpers(self):
        secret = Mock(return_value='internal-value')
        with patch('mage_ai.data_preparation.shared.secrets.get_secret_value', secret):
            self.assertEqual(get_template_vars()['mage_secret_var']('internal'), 'internal-value')
        with patch.dict(os.environ, {'INTERNAL_TEST_VALUE': 'local-value'}):
            self.assertEqual(get_template_vars_no_db()['env_var']('INTERNAL_TEST_VALUE'), 'local-value')
            self.assertEqual(EnvironmentVariableLoader().get('INTERNAL_TEST_VALUE'), 'local-value')

    def test_azure_db_setting_fails_and_postgres_credentials_work(self):
        with patch.dict(os.environ, {'AZURE_SECRET_DB_CONN_URL': 'private-secret-name'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'AZURE_SECRET_DB_CONN_URL has been removed') as error:
                get_postgres_connection_url()
            self.assertNotIn('private-secret-name', str(error.exception))
        with patch.dict(os.environ, {
            'DB_USER': 'test', 'DB_PASS': 'test', 'DB_NAME': 'internal',
        }, clear=True):
            self.assertEqual(get_postgres_connection_url(),
                             'postgresql+psycopg2://test:test@127.0.0.1:5432/internal')
