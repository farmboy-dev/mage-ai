import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

from mage_ai.io.config import ConfigKey
from mage_ai.io.s3 import S3
from mage_ai.services.aws.s3.s3 import Client
from mage_ai.data_preparation.storage.s3_storage import S3Storage
from mage_ai.streaming.sinks.amazon_s3 import AmazonS3Config, AmazonS3Sink


class CompatibleS3Test(unittest.TestCase):
    def test_local_roundtrip_and_download(self):
        objects = {}
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_PUT(self):
                requests.append((self.path, self.headers.get('Authorization')))
                objects[self.path] = self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200)
                self.send_header('ETag', '"test"')
                self.end_headers()

            def do_HEAD(self):
                self.do_GET(head=True)

            def do_GET(self, head=False):
                requests.append((self.path, self.headers.get('Authorization')))
                data = objects[self.path]
                self.send_response(200)
                self.send_header('Content-Length', str(len(data)))
                self.send_header('ETag', '"test"')
                self.end_headers()
                if not head:
                    self.wfile.write(data)

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        endpoint = f'http://127.0.0.1:{server.server_port}'
        options = dict(endpoint_url=endpoint, aws_access_key_id='local-access',
                       aws_secret_access_key='local-secret', region_name='us-east-1')
        try:
            config = {key: None for key in ConfigKey}
            config.update({ConfigKey.AWS_ENDPOINT: endpoint,
                           ConfigKey.AWS_ACCESS_KEY_ID: 'local-access',
                           ConfigKey.AWS_SECRET_ACCESS_KEY: 'local-secret',
                           ConfigKey.AWS_REGION: 'us-east-1',
                           ConfigKey.AWS_S3_ADDRESSING_STYLE: 'path'})
            io = S3.with_config(config)
            io.export(pd.DataFrame({'value': [1, 2]}), 'local-bucket', 'rows.csv')
            self.assertEqual(io.load('local-bucket', 'rows.csv')['value'].tolist(), [1, 2])
            client = Client('local-bucket', **options)
            with tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / 'download.csv'
                client.download_file('rows.csv', str(target))
                self.assertEqual(target.read_bytes(), objects['/local-bucket/rows.csv'])
            self.assertEqual(client.resource().meta.client.meta.endpoint_url, endpoint)
            storage = S3Storage(bucket='local-bucket', **options)
            storage.write_json_file('s3://local-bucket/data.json', {'result': 42})
            self.assertEqual(storage.read_json_file('s3://local-bucket/data.json'), {'result': 42})
            sink = object.__new__(AmazonS3Sink)
            sink.timer = Mock()
            sink.config = AmazonS3Config(bucket='local-bucket', prefix='', **options)
            sink.init_storage_client()
            sink.upload_data_with_client(b'stream', 'stream.txt')
            self.assertEqual(objects['/local-bucket/stream.txt'], b'stream')
            self.assertTrue(all(path.startswith('/local-bucket/') for path, _ in requests))
            self.assertTrue(all('AWS4-HMAC-SHA256' in auth for _, auth in requests))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_injected_client_does_not_create_an_aws_connection(self):
        with patch('mage_ai.services.aws.s3.s3.boto3.client') as constructor:
            client = Mock()
            self.assertIs(Client('bucket', client=client).client, client)
            constructor.assert_not_called()

    def test_environment_endpoint_for_remote_variables(self):
        with patch.dict(os.environ, {'AWS_ENDPOINT_URL_S3': 'http://storage.internal:9000',
                                     'AWS_ACCESS_KEY_ID': 'local',
                                     'AWS_SECRET_ACCESS_KEY': 'local'}):
            storage = S3Storage(dirpath='s3://bucket/data')
            self.assertEqual(storage.client.client.meta.endpoint_url, 'http://storage.internal:9000')
            self.assertEqual(storage.client.client.meta.config.s3['addressing_style'], 'path')

    def test_integration_clients_keep_endpoint_and_session_token(self):
        from mage_integrations.sources.amazon_s3 import AmazonS3 as Source
        from mage_integrations.destinations.amazon_s3 import AmazonS3 as Destination

        for cls in (Source, Destination):
            connector = object.__new__(cls)
            connector.config = {
                'aws_endpoint': 'http://storage.internal:9000',
                'aws_region': 'us-east-1',
                'aws_access_key_id': 'local',
                'aws_secret_access_key': 'secret',
                'aws_session_token': 'token',
                'aws_s3_addressing_style': 'path',
            }
            client = connector.build_client()
            self.assertEqual(client.meta.endpoint_url, 'http://storage.internal:9000')
            self.assertEqual(client.meta.config.s3['addressing_style'], 'path')
            self.assertEqual(client._request_signer._credentials.token, 'token')

    def test_partial_botocore_options_preserve_path_style(self):
        from botocore.config import Config
        from mage_ai.services.aws.s3.config import client_options

        original = Config(s3={'payload_signing_enabled': True}, max_pool_connections=50)
        options = client_options(endpoint_url='http://minio.internal:9000', config=original)
        self.assertEqual(options['config'].s3, {
            'payload_signing_enabled': True, 'addressing_style': 'path',
        })
        self.assertEqual(options['config'].max_pool_connections, 50)
        self.assertEqual(original.s3, {'payload_signing_enabled': True})
        options = client_options(
            endpoint_url='http://minio.internal:9000', addressing_style='path',
            config=Config(s3={'addressing_style': 'virtual'}),
        )
        self.assertEqual(options['config'].s3['addressing_style'], 'path')
        with self.assertRaisesRegex(ValueError, 'addressing_style'):
            client_options(addressing_style='invalid')
