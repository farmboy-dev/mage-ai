import posixpath
from urllib.parse import urlsplit

import boto3
from botocore.config import Config

from mage_integrations.destinations.delta_lake.base import DeltaLake as BaseDeltaLake
from mage_integrations.destinations.delta_lake.base import main


class DeltaLakeS3(BaseDeltaLake):
    @property
    def bucket(self):
        return self.config['bucket']

    @property
    def region(self):
        return self.config.get('aws_region') or 'us-west-2'

    @property
    def endpoint(self):
        endpoint = self.config.get('aws_endpoint')
        if endpoint:
            parsed = urlsplit(endpoint)
            if parsed.scheme not in ('http', 'https') or not parsed.netloc:
                raise ValueError('S3 endpoint must be an HTTP or HTTPS URL.')
            if parsed.scheme == 'http' and self.config.get('aws_allow_http') is not True:
                raise ValueError('HTTP S3 endpoints require aws_allow_http=true.')
        return endpoint

    @property
    def addressing_style(self):
        style = self.config.get('aws_s3_addressing_style') or 'path'
        if style not in ('path', 'virtual'):
            raise ValueError('S3 addressing style must be path or virtual.')
        return style

    @property
    def table_object_key_path(self):
        prefix = (self.config.get('object_key_path') or '').strip('/')
        table = self.table_name.strip('/')
        if not table or any(part in ('.', '..') for part in (prefix + '/' + table).split('/')):
            raise ValueError('A valid table path is required.')
        return posixpath.join(prefix, table)

    @property
    def delta_log_object_key_path(self):
        return f'{self.table_object_key_path}/_delta_log'

    def build_storage_options(self):
        options = {
            'AWS_ACCESS_KEY_ID': self.config['aws_access_key_id'],
            'AWS_SECRET_ACCESS_KEY': self.config['aws_secret_access_key'],
            'AWS_REGION': self.region,
            'AWS_S3_ALLOW_UNSAFE_RENAME': 'true',
            'AWS_S3_ADDRESSING_STYLE': self.addressing_style,
            'AWS_VIRTUAL_HOSTED_STYLE_REQUEST': str(self.addressing_style == 'virtual').lower(),
            'AWS_ALLOW_HTTP': str(self.config.get('aws_allow_http') is True).lower(),
        }
        if self.endpoint:
            options['AWS_ENDPOINT_URL'] = self.endpoint
        if self.config.get('aws_session_token'):
            options['AWS_SESSION_TOKEN'] = self.config['aws_session_token']
        return options

    def build_table_uri(self, stream):
        return f's3://{self.bucket}/{self.table_object_key_path}'

    def build_client(self):
        return boto3.client(
            's3',
            aws_access_key_id=self.config['aws_access_key_id'],
            aws_secret_access_key=self.config['aws_secret_access_key'],
            aws_session_token=self.config.get('aws_session_token'),
            endpoint_url=self.endpoint,
            region_name=self.region,
            config=Config(
                retries={'max_attempts': 10, 'mode': 'standard'},
                s3={'addressing_style': self.addressing_style},
            ),
        )

    def check_and_create_delta_log(self, stream):
        client = self.build_client()
        response = client.list_objects_v2(
            Bucket=self.bucket, Prefix=f'{self.delta_log_object_key_path}/', MaxKeys=1,
        )
        if response.get('Contents'):
            return True
        response = client.list_objects_v2(
            Bucket=self.bucket, Prefix=f'{self.table_object_key_path}/', MaxKeys=1,
        )
        if response.get('Contents'):
            raise ValueError('The table path contains files without a Delta log. Use an empty path.')
        return False

    def test_connection(self):
        self.build_client().head_bucket(Bucket=self.bucket)


if __name__ == '__main__':
    main(DeltaLakeS3)
