import os
import unittest
import uuid
from unittest.mock import Mock, patch

import pyarrow as pa
from deltalake import DeltaTable

from mage_integrations.destinations.delta_lake.writer import write_deltalake
from mage_integrations.destinations.delta_lake_s3 import DeltaLakeS3


def config(**kwargs):
    return dict(aws_access_key_id='test', aws_secret_access_key='test-secret',
                bucket='test-bucket', object_key_path='prefix', table='data', **kwargs)


class DeltaS3ConfigTest(unittest.TestCase):
    def test_endpoint_and_credentials_reach_both_clients(self):
        destination = DeltaLakeS3(config=config(aws_endpoint='https://minio.internal',
                                                aws_session_token='test-token'))
        options = destination.build_storage_options()
        self.assertEqual(options['AWS_ENDPOINT_URL'], 'https://minio.internal')
        self.assertEqual(options['AWS_SESSION_TOKEN'], 'test-token')
        self.assertEqual(options['AWS_VIRTUAL_HOSTED_STYLE_REQUEST'], 'false')
        with patch('boto3.client') as client:
            destination.build_client()
        self.assertEqual(client.call_args.kwargs['endpoint_url'], options['AWS_ENDPOINT_URL'])
        self.assertEqual(client.call_args.kwargs['aws_session_token'], options['AWS_SESSION_TOKEN'])
        self.assertEqual(client.call_args.kwargs['config'].s3['addressing_style'], 'path')

    def test_http_requires_explicit_opt_in(self):
        destination = DeltaLakeS3(config=config(aws_endpoint='http://minio:9000'))
        for method in (destination.build_client, destination.build_storage_options):
            with self.assertRaisesRegex(ValueError, 'aws_allow_http'):
                method()
        destination.config['aws_allow_http'] = True
        self.assertEqual(destination.build_storage_options()['AWS_ALLOW_HTTP'], 'true')

    def test_uri_and_existing_files_are_preserved(self):
        destination = DeltaLakeS3(config=config())
        self.assertEqual(destination.build_table_uri('stream'), 's3://test-bucket/prefix/data')
        client = Mock()
        client.list_objects_v2.side_effect = [{}, {'Contents': [{'Key': 'prefix/data/existing'}]}]
        with patch.object(destination, 'build_client', return_value=client):
            with self.assertRaisesRegex(ValueError, 'without a Delta log'):
                destination.check_and_create_delta_log('stream')
        client.delete_object.assert_not_called()
        self.assertEqual(client.list_objects_v2.call_args.kwargs['Prefix'], 'prefix/data/')


@unittest.skipUnless(os.getenv('MAGE_TEST_MINIO_ENDPOINT'), 'Requires a disposable MinIO server')
class DeltaMinIOTest(unittest.TestCase):
    def setUp(self):
        self.destination = DeltaLakeS3(config=dict(
            aws_access_key_id=os.environ['MAGE_TEST_MINIO_ACCESS_KEY'],
            aws_secret_access_key=os.environ['MAGE_TEST_MINIO_SECRET_KEY'],
            aws_endpoint=os.environ['MAGE_TEST_MINIO_ENDPOINT'], aws_allow_http=True,
            aws_region='us-east-1', bucket='mage-delta-test-' + uuid.uuid4().hex,
            object_key_path='tables', table='sample',
        ))
        self.client = self.destination.build_client()
        self.client.create_bucket(Bucket=self.destination.bucket)
        self.addCleanup(self.cleanup_bucket)

    def cleanup_bucket(self):
        for page in self.client.get_paginator('list_objects_v2').paginate(Bucket=self.destination.bucket):
            for obj in page.get('Contents', []):
                self.client.delete_object(Bucket=self.destination.bucket, Key=obj['Key'])
        self.client.delete_bucket(Bucket=self.destination.bucket)

    def test_actual_s3_partition_write_and_transaction_history(self):
        d = self.destination
        d.test_connection()
        self.assertFalse(d.check_and_create_delta_log('stream'))
        path, options = d.build_table_uri('stream'), d.build_storage_options()
        write_deltalake(path, pa.table({'id': [1, 2], 'part': ['a', 'b']}),
                        partition_by=['part'], storage_options=options)
        write_deltalake(path, pa.table({'id': [3], 'part': ['a']}),
                        mode='append', storage_options=options)
        history = self.client.get_object(Bucket=d.bucket,
                                        Key=d.delta_log_object_key_path + '/00000000000000000001.json')['Body'].read()
        write_deltalake(path, pa.table({'id': [4], 'part': ['a']}),
                        mode='overwrite', storage_options=options)
        self.assertEqual(sorted(DeltaTable(path, storage_options=options).to_pyarrow_table()
                                .column('id').to_pylist()), [2, 4])
        self.assertEqual(self.client.get_object(Bucket=d.bucket,
                         Key=d.delta_log_object_key_path + '/00000000000000000001.json')['Body'].read(), history)
        self.assertTrue(d.check_and_create_delta_log('stream'))

    def test_destination_export(self):
        d = self.destination
        d.schemas = {'stream': {'properties': {'id': {'type': ['integer']},
                                              'name': {'type': ['string']}}}}
        d.partition_keys = {'stream': []}
        d.export_batch_data([{'record': {'id': 1, 'name': 'first'}}], 'stream')
        d.export_batch_data([{'record': {'id': 2, 'name': 'second'}}], 'stream')
        rows = d.get_table_for_stream('stream').to_pyarrow_table().to_pylist()
        self.assertEqual(sorted(row['id'] for row in rows), [1, 2])

    def test_existing_non_delta_object_is_not_deleted(self):
        d = self.destination
        key = d.table_object_key_path + '/keep.txt'
        self.client.put_object(Bucket=d.bucket, Key=key, Body=b'keep')
        with self.assertRaises(ValueError):
            d.check_and_create_delta_log('stream')
        self.assertEqual(self.client.get_object(Bucket=d.bucket, Key=key)['Body'].read(), b'keep')

    def test_export_preserves_nullable_types_and_partition_scope(self):
        d = self.destination
        d.schemas = {'stream': {'properties': {
            'id': {'type': ['integer', 'null']},
            'enabled': {'type': ['boolean', 'null']},
            'part': {'type': ['string', 'null']},
        }}}
        d.partition_keys = {'stream': ['part']}
        d.export_batch_data([
            {'record': {'id': 9007199254740993, 'enabled': False, 'part': 'keep'}},
            {'record': {'id': None, 'enabled': None, 'part': None}},
            {'record': {'id': 3, 'enabled': True, 'part': "a'b"}},
        ], 'stream')
        rows = d.get_table_for_stream('stream').to_pyarrow_table().to_pylist()
        self.assertIn({'id': 9007199254740993, 'enabled': False, 'part': 'keep'}, rows)
        self.assertIn({'id': None, 'enabled': None, 'part': None}, rows)
        d.config['mode'] = 'overwrite'
        d.export_batch_data([{'record': {'id': 4, 'enabled': False, 'part': "a'b"}}], 'stream')
        rows = d.get_table_for_stream('stream').to_pyarrow_table().to_pylist()
        self.assertEqual(len(rows), 3)
        self.assertIn({'id': 4, 'enabled': False, 'part': "a'b"}, rows)
        self.assertIn({'id': 9007199254740993, 'enabled': False, 'part': 'keep'}, rows)
        self.assertIn({'id': None, 'enabled': None, 'part': None}, rows)

    def test_authentication_error_is_not_missing_table(self):
        d = self.destination
        d.config['aws_secret_access_key'] = 'incorrect-test-secret'
        with self.assertRaises(Exception):
            d.test_connection()
        with self.assertRaises(Exception):
            d.get_table_for_stream('stream')
