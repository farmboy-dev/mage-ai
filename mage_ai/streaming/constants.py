from mage_ai.shared.enum import StrEnum

DEFAULT_BATCH_SIZE = 100
DEFAULT_TIMEOUT_MS = 500


class SourceType(StrEnum):
    ACTIVEMQ = 'activemq'
    INFLUXDB = 'influxdb'
    KAFKA = 'kafka'
    NATS = 'nats'
    RABBITMQ = 'rabbitmq'
    MONGODB = 'mongodb'


class SinkType(StrEnum):
    ACTIVEMQ = 'activemq'
    AMAZON_S3 = 'amazon_s3'
    CLICKHOUSE = 'clickhouse'
    DUCKDB = 'duckdb'
    DUMMY = 'dummy'
    ELASTICSEARCH = 'elasticsearch'
    INFLUXDB = 'influxdb'
    KAFKA = 'kafka'
    MONGODB = 'mongodb'
    MSSQL = 'mssql'
    MYSQL = 'mysql'
    OPENSEARCH = 'opensearch'
    ORACLEDB = 'oracledb'
    POSTGRES = 'postgres'
    RABBITMQ = 'rabbitmq'
    TRINO = 'trino'


GENERIC_IO_SINK_TYPES = frozenset([
    SinkType.CLICKHOUSE,
    SinkType.DUCKDB,
    SinkType.MSSQL,
    SinkType.MYSQL,
    SinkType.TRINO,
])
