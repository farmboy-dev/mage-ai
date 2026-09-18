import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from mage_ai.api.resources.DataProviderResource import DATA_PROVIDERS
from mage_ai.api.resources.BlockResource import validate_connector_payload
from mage_ai.api.errors import ApiError
from mage_ai.data_integrations.destinations.constants import DESTINATIONS
from mage_ai.data_integrations.sources.constants import SOURCES, SQL_SOURCES
from mage_ai.data_integrations.utils.settings import get_uuid
from mage_ai.data_preparation.models.block import Block
from mage_ai.data_preparation.models.block.data_integration.utils import (
    destination_module, source_module,
)
from mage_ai.data_preparation.models.block.sql import execute_sql_code
from mage_ai.data_preparation.models.constants import BlockType, PipelineType
from mage_ai.data_preparation.models.pipelines.integration_pipeline import IntegrationPipeline
from mage_ai.data_preparation.templates.constants import TEMPLATES, TEMPLATES_ONLY_FOR_V2
from mage_ai.data_preparation.templates.template import fetch_template_source
from mage_ai.server.api.integration_sources import build_integration_module_info
from mage_ai.shared.cloud_features import (
    REMOVED_CONNECTORS, reject_removed_connector_config,
)
from mage_ai.streaming.sinks.sink_factory import SinkFactory


class RemovedCloudConnectorTest(unittest.TestCase):
    def test_invalid_api_payload_is_a_client_error(self):
        with self.assertRaises(ApiError) as raised:
            validate_connector_payload({'config': {'data_source': 'bigquery'}})
        self.assertEqual(raised.exception.code, 400)
        self.assertIn('removed from this internal deployment', raised.exception.message)

    def test_stale_search_cache_hides_only_removed_builtin_templates(self):
        from mage_ai.services.search.block_action_objects import search

        cache = Mock()
        cache.load_all_data.return_value = {
            'mage_template': {
                'legacy': {'name': 'BigQuery', 'path': 'data_loaders/bigquery.py'},
                's3': {'name': 'Amazon S3', 'path': 'data_loaders/s3.py'},
            },
            'block_file': {'custom': {'uuid': 'custom', 'content': 'bigquery migration notes'}},
        }
        with patch('mage_ai.services.search.block_action_objects.BlockActionObjectCache.initialize_cache',
                   new=AsyncMock(return_value=cache)):
            results = asyncio.run(search('bigquery', ratio=0))
        self.assertEqual({x['uuid'] for x in results}, {'s3', 'custom'})

    def test_catalogs_exclude_removed_connectors_and_keep_internal_options(self):
        for catalog in [SOURCES, SQL_SOURCES, DESTINATIONS]:
            self.assertFalse(REMOVED_CONNECTORS.intersection(get_uuid(x) for x in catalog))
        self.assertIn('amazon_s3', {get_uuid(x) for x in SOURCES})
        self.assertIn('amazon_s3', {get_uuid(x) for x in DESTINATIONS})
        self.assertIn('postgresql', {get_uuid(x) for x in SQL_SOURCES})
        self.assertFalse(REMOVED_CONNECTORS.intersection(DATA_PROVIDERS))
        self.assertIn('spark', DATA_PROVIDERS)
        self.assertIn('postgres', DATA_PROVIDERS)

    def test_registered_template_files_exist_and_exclude_removed_paths(self):
        root = Path(__file__).parents[2] / 'data_preparation' / 'templates'
        for template in TEMPLATES + TEMPLATES_ONLY_FOR_V2:
            path = template['path']
            self.assertTrue((root / path).is_file(), path)
            reject_removed_connector_config({'template_path': path})

    def test_removed_templates_fail_before_fallback_for_all_pipeline_types(self):
        for provider in REMOVED_CONNECTORS:
            for pipeline_type in [PipelineType.PYTHON, PipelineType.PYSPARK,
                                  PipelineType.STREAMING]:
                with self.subTest(provider=provider, pipeline=pipeline_type):
                    with self.assertRaisesRegex(ValueError, 'removed from this internal deployment'):
                        fetch_template_source(BlockType.DATA_LOADER, {'data_source': provider},
                                              pipeline_type=pipeline_type)

    def test_template_paths_and_integration_payloads_are_checked(self):
        for config in [
            {'template_path': 'data_loaders/deltalake/gcs.py'},
            {'configuration': {'data_provider': 'bigquery'}},
            {'template_variables': {'name': 'Google Sheets'}},
            {'configuration': {'data_integration': {'source': 'snowflake'}}},
        ]:
            with self.assertRaisesRegex(ValueError, 'removed from this internal deployment'):
                reject_removed_connector_config(config)
        reject_removed_connector_config({'data_source': 's3', 'config': {'bucket': 'bigquery'}})

    def test_integration_imports_and_direct_catalog_lookup_fail_before_loading(self):
        with patch('importlib.import_module', side_effect=AssertionError('Unexpected import')):
            for provider in REMOVED_CONNECTORS:
                for loader in [source_module, destination_module]:
                    with self.assertRaisesRegex(ValueError, 'removed from this internal deployment'):
                        loader(provider)
                with self.assertRaisesRegex(ValueError, 'removed from this internal deployment'):
                    build_integration_module_info('sources', {'name': provider, 'uuid': provider})

    def test_legacy_pipeline_does_not_swallow_removal_error_in_path_fallback(self):
        pipeline = SimpleNamespace(source_uuid='bigquery', destination_uuid='snowflake')
        for prop in ['source', 'destination', 'source_file_path', 'destination_file_path']:
            with self.assertRaisesRegex(ValueError, 'removed from this internal deployment'):
                getattr(IntegrationPipeline, prop).fget(pipeline)

    def test_sql_rejected_before_configuration_or_client_initialization(self):
        block = SimpleNamespace(configuration={'data_provider': 'redshift'})
        with self.assertRaisesRegex(ValueError, 'removed from this internal deployment'):
            execute_sql_code(block, 'SELECT 1')

    def test_streaming_rejected_before_factory_import(self):
        for provider in ['bigquery', 'redshift', 'snowflake', 'google_cloud_storage']:
            with self.assertRaisesRegex(ValueError, 'removed from this internal deployment'):
                SinkFactory.get_sink({'connector_type': provider})

    def test_block_creation_and_execution_rejected_before_side_effects(self):
        with self.assertRaisesRegex(ValueError, 'removed from this internal deployment'):
            Block.create('legacy', 'data_loader', '/unused', config={'data_source': 'bigquery'})
        block = SimpleNamespace(configuration={'data_source': 'google_sheets'})
        with self.assertRaisesRegex(ValueError, 'removed from this internal deployment'):
            Block.execute_sync(block)

    def test_non_connector_edits_are_not_rejected_by_policy(self):
        reject_removed_connector_config({'name': 'Legacy pipeline block'})
        reject_removed_connector_config({'content': 'from mage_ai.io.bigquery import BigQuery'})
