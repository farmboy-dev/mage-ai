from dataclasses import dataclass

import boto3

from mage_ai.services.aws.s3.config import client_options

from mage_ai.streaming.sinks.base_object_storage import (
    BaseObjectStorageConfig,
    BaseObjectStorageSink,
)


@dataclass
class AmazonS3Config(BaseObjectStorageConfig):
    endpoint_url: str = None
    region_name: str = None
    aws_access_key_id: str = None
    aws_secret_access_key: str = None
    aws_session_token: str = None
    addressing_style: str = None


class AmazonS3Sink(BaseObjectStorageSink):
    config_class = AmazonS3Config

    def init_storage_client(self):
        self.client = boto3.client('s3', **client_options(**self.config.to_dict()))

    def upload_data_with_client(
        self,
        buffer,
        key: str,
    ):
        self.client.put_object(Body=buffer, Bucket=self.config.bucket, Key=key)
