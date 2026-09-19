import unittest
from unittest.mock import Mock, patch

from mage_integrations.sources.couchbase import Couchbase


class CouchbaseSourceTest(unittest.TestCase):
    def setUp(self):
        self.source = Couchbase(config=dict(bucket='test', scope='scope',
            connection_string='couchbase://localhost', username='test', password='test-password'))

    def test_connection_configuration(self):
        with patch('mage_integrations.sources.couchbase.CouchbaseConnection') as connection:
            self.source.build_connection()
        connection.assert_called_once_with(**self.source.config)

    def test_discover_inferred_schema(self):
        connection = Mock()
        connection.get_all_collections.return_value = ['users']
        connection.load.return_value = [[{'properties': {
            'name': {'type': 'string'}, 'missing': {'type': 'missing'},
            'count': {'type': ['number', 'null']},
        }}]]
        with patch.object(self.source, 'build_connection', return_value=connection):
            result = self.source.discover().to_dict()['streams']
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['stream'], 'users')
        self.assertEqual(result[0]['schema']['properties']['name']['type'], ['null', 'string'])
        self.assertIn('string', result[0]['schema']['properties']['missing']['type'])
        self.assertIn('INFER `users`', connection.load.call_args.args[0])

    def test_discover_combined_documents(self):
        self.source.config['strategy'] = 'combine'
        connection = Mock()
        connection.get_all_collections.return_value = ['users']
        connection.load.return_value = [[{'properties': {'name': {'type': 'string'}}}]]
        with patch.object(self.source, 'build_connection', return_value=connection):
            result = self.source.discover().to_dict()['streams'][0]
        self.assertIn('_document', result['schema']['properties'])
        self.assertEqual(self.source.update_column_names(['_document']), ['*'])
        self.assertEqual(self.source._convert_to_rows(['_document'], [{'users': {'id': 1}}]),
                         [{'_document': {'id': 1}}])

    def test_discovery_error_propagates(self):
        connection = Mock()
        connection.get_all_collections.side_effect = RuntimeError('Access denied')
        with patch.object(self.source, 'build_connection', return_value=connection):
            with self.assertRaisesRegex(RuntimeError, 'Access denied'):
                self.source.discover()
