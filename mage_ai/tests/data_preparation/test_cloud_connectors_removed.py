import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch

from mage_ai.api.errors import ApiError
from mage_ai.api.resources.BlockResource import validate_connector_payload
from mage_ai.data_preparation.models.block.data_integration.utils import source_module, destination_module
from mage_ai.data_preparation.templates.constants import TEMPLATES, TEMPLATES_ONLY_FOR_V2
from mage_ai.shared.supported_features import validate_connector, validate_connector_config


class SupportedConnectorTest(unittest.TestCase):
    def test_unknown_api_payload(self):
        for key in ['data_source', 'data_provider', 'source', 'destination']:
            with self.assertRaises(ApiError) as error:
                validate_connector_payload({'config': {key: 'unregistered_connector'}})
            self.assertEqual(error.exception.code, 400)
            self.assertIn('Unsupported connector', error.exception.message)

    def test_directional_integration_validation(self):
        validate_connector('github', 'source')
        with self.assertRaisesRegex(ValueError, 'Unsupported connector'):
            validate_connector('github', 'destination')
        validate_connector('kafka', 'destination')
        with self.assertRaisesRegex(ValueError, 'Unsupported connector'):
            validate_connector('kafka', 'source')
        for kind in ['source', 'destination']:
            validate_connector('amazon_s3', kind)
            validate_connector('postgresql', kind)
        for value in ['api', 'sftp']:
            validate_connector(value, 'source')

    def test_module_loaders_use_directional_catalogs(self):
        with patch('importlib.import_module') as load:
            source_module('github')
            load.assert_called_with('mage_integrations.sources.github')
            destination_module('kafka')
            load.assert_called_with('mage_integrations.destinations.kafka')
            with self.assertRaisesRegex(ValueError, 'Unsupported connector'):
                destination_module('github')
            with self.assertRaisesRegex(ValueError, 'Unsupported connector'):
                source_module('kafka')

    def test_unknown_imports_fail_before_loading(self):
        with patch('importlib.import_module', side_effect=AssertionError('Unexpected import')):
            for loader in [source_module, destination_module]:
                with self.assertRaisesRegex(ValueError, 'Unsupported connector'):
                    loader('unregistered_connector')

    def test_registered_templates_are_valid(self):
        for template in TEMPLATES + TEMPLATES_ONLY_FOR_V2:
            with self.subTest(path=template['path']):
                validate_connector_config({'template_path': template['path']})

    def test_template_path_and_integration_direction(self):
        for path in ['../secret', '/etc/passwd', 'data_loaders/missing.py']:
            with self.assertRaisesRegex(ValueError, 'Unsupported template'):
                validate_connector_config({'template_path': path})
        for direction in ['sources', 'destinations']:
            config = {'template_path': f'data_integrations/{direction}/base',
                      'template_type': 'data_integration',
                      'template_variables': {'name': 'Amazon S3'}}
            validate_connector_config(config)
            config['template_variables'] = {'name': 'Unregistered Connector'}
            with self.assertRaisesRegex(ValueError, 'Unsupported connector'):
                validate_connector_config(config)

    def test_custom_content_is_not_a_connector_id(self):
        validate_connector_config({'name': 'unregistered_connector', 'content': 'example',
                                   'template_variables': {'name': 'My template'}})

    def test_cache_filters_only_unregistered_builtin_templates(self):
        from mage_ai.services.search.block_action_objects import search
        cache = Mock()
        cache.load_all_data.return_value = {
            'mage_template': {
                'missing': {'name': 'Missing', 'path': 'data_loaders/missing.py'},
                's3': {'name': 'Amazon S3', 'path': 'data_loaders/s3.py'},
            },
            'block_file': {'custom': {'uuid': 'custom', 'content': 'missing notes'}},
        }
        with patch('mage_ai.services.search.block_action_objects.BlockActionObjectCache.initialize_cache',
                   new=AsyncMock(return_value=cache)):
            results = asyncio.run(search('missing', ratio=0))
        self.assertEqual({x['uuid'] for x in results}, {'s3', 'custom'})
