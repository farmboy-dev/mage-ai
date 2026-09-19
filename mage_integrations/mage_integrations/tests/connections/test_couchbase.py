import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from mage_integrations.connections.couchbase import Couchbase
from mage_integrations.sources.couchbase import Couchbase as CouchbaseSource


class CouchbaseConnectionTest(unittest.TestCase):
    def setUp(self):
        self.connection = Couchbase(bucket='test', scope='scope',
            connection_string='couchbase://localhost', username='test', password='test-password')

    def test_bucket_authentication_and_scope(self):
        with patch('mage_integrations.connections.couchbase.PasswordAuthenticator') as auth, \
                patch('mage_integrations.connections.couchbase.Cluster') as cluster:
            self.connection.get_scope()
        auth.assert_called_once_with('test', 'test-password')
        self.assertEqual(cluster.call_args.args[0], 'couchbase://localhost')
        cluster.return_value.bucket.assert_called_once_with('test')
        cluster.return_value.bucket.return_value.scope.assert_called_once_with('scope')

    def test_collection_filter(self):
        bucket = Mock()
        bucket.collections.return_value.get_all_scopes.return_value = [
            SimpleNamespace(name='other', collections=[SimpleNamespace(name='hidden')]),
            SimpleNamespace(name='scope', collections=[SimpleNamespace(name='users')]),
        ]
        with patch.object(self.connection, 'get_bucket', return_value=bucket):
            self.assertEqual(self.connection.get_all_collections(), ['users'])

    def test_query_rows_and_errors(self):
        scope = Mock()
        scope.query.return_value.rows.return_value = iter([{'id': 1}])
        with patch.object(self.connection, 'get_scope', return_value=scope):
            self.assertEqual(self.connection.load('SELECT 1 AS id'), [{'id': 1}])
            scope.query.side_effect = RuntimeError('Query failed')
            with self.assertRaisesRegex(RuntimeError, 'Query failed'):
                self.connection.load('invalid query')

    def test_missing_scope_is_explicit(self):
        bucket = Mock()
        bucket.collections.return_value.get_all_scopes.return_value = []
        with patch.object(self.connection, 'get_bucket', return_value=bucket):
            with self.assertRaisesRegex(ValueError, 'does not exist'):
                self.connection.get_all_collections()


@unittest.skipUnless(os.getenv('MAGE_TEST_COUCHBASE_URL'), 'Requires a disposable Couchbase server')
class CouchbaseServerTest(unittest.TestCase):
    def config(self):
        return dict(bucket='mage_test', scope='_default',
            connection_string=os.environ['MAGE_TEST_COUCHBASE_URL'],
            username=os.environ['MAGE_TEST_COUCHBASE_USER'],
            password=os.environ['MAGE_TEST_COUCHBASE_PASSWORD'])

    def test_collections_and_query(self):
        connection = Couchbase(**self.config())
        self.assertIn('_default', connection.get_all_collections())
        self.assertEqual(connection.load('SELECT 42 AS answer'), [{'answer': 42}])
        rows = connection.load('SELECT d.id FROM `_default` d ORDER BY d.id')
        self.assertEqual(rows, [{'id': 1}, {'id': 2}])

    def test_bad_credentials(self):
        config = self.config()
        config['password'] = 'incorrect-test-password'
        with self.assertRaises(Exception):
            CouchbaseSource(config=config).test_connection()

    def test_missing_bucket(self):
        config = self.config()
        config['bucket'] = 'missing_bucket'
        with self.assertRaises(Exception):
            CouchbaseSource(config=config).test_connection()

    def test_source_discover(self):
        source = CouchbaseSource(config=self.config())
        streams = source.discover().to_dict()['streams']
        self.assertIn('_default', [stream['stream'] for stream in streams])

    def test_source_connection_checks_scope(self):
        config = self.config()
        CouchbaseSource(config=config).test_connection()
        config['scope'] = 'missing_scope'
        with self.assertRaisesRegex(ValueError, 'does not exist'):
            CouchbaseSource(config=config).test_connection()
