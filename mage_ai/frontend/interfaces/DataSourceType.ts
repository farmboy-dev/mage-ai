import { BlockTypeEnum } from './BlockType';

export enum DataSourceTypeEnum {
  ACTIVEMQ = 'activemq',
  API = 'api',
  CLICKHOUSE = 'clickhouse',
  DRUID = 'druid',
  DUCKDB = 'duckdb',
  DUMMY = 'dummy',
  ELASTICSEARCH = 'elasticsearch',
  FILE = 'file',
  GENERIC = 'generic',
  INFLUXDB = 'influxdb',
  KAFKA = 'kafka',
  MONGODB = 'mongodb',
  MSSQL = 'mssql',
  MYSQL = 'mysql',
  NATS = 'nats',
  OPENSEARCH = 'opensearch',
  ORACLEDB = 'oracledb',
  PINOT = 'pinot',
  POSTGRES = 'postgres',
  RABBITMQ = 'rabbitmq',
  S3 = 's3',
  TRINO = 'trino',
}

export const DATA_SOURCE_TYPE_HUMAN_READABLE_NAME_MAPPING = {
  [DataSourceTypeEnum.ACTIVEMQ]: 'ActiveMQ',
  [DataSourceTypeEnum.API]: 'API',
  [DataSourceTypeEnum.CLICKHOUSE]: 'ClickHouse',
  [DataSourceTypeEnum.DRUID]: 'Druid',
  [DataSourceTypeEnum.DUCKDB]: 'DuckDB',
  [DataSourceTypeEnum.DUMMY]: 'Dummy',
  [DataSourceTypeEnum.ELASTICSEARCH]: 'ElasticSearch',
  [DataSourceTypeEnum.FILE]: 'Local file',
  [DataSourceTypeEnum.GENERIC]: 'Generic (no template)',
  [DataSourceTypeEnum.INFLUXDB]: 'InfluxDB',
  [DataSourceTypeEnum.KAFKA]: 'Kafka',
  [DataSourceTypeEnum.MONGODB]: 'MongoDB',
  [DataSourceTypeEnum.MSSQL]: 'Microsoft SQL Server',
  [DataSourceTypeEnum.MYSQL]: 'MySQL',
  [DataSourceTypeEnum.NATS]: 'NATS',
  [DataSourceTypeEnum.OPENSEARCH]: 'OpenSearch',
  [DataSourceTypeEnum.ORACLEDB]: 'OracleDB',
  [DataSourceTypeEnum.PINOT]: 'Pinot',
  [DataSourceTypeEnum.POSTGRES]: 'PostgreSQL',
  [DataSourceTypeEnum.RABBITMQ]: 'RabbitMQ',
  [DataSourceTypeEnum.S3]: 'Amazon S3',
  [DataSourceTypeEnum.TRINO]: 'Trino',
};

export const DATA_SOURCE_TYPES: { [blockType in BlockTypeEnum]?: DataSourceTypeEnum[] } = {
  [BlockTypeEnum.DATA_LOADER]: [
    DataSourceTypeEnum.GENERIC,
    DataSourceTypeEnum.FILE,
    DataSourceTypeEnum.API,
    DataSourceTypeEnum.DRUID,
    DataSourceTypeEnum.MYSQL,
    DataSourceTypeEnum.ORACLEDB,
    DataSourceTypeEnum.PINOT,
    DataSourceTypeEnum.POSTGRES,
    DataSourceTypeEnum.S3,
    DataSourceTypeEnum.MONGODB,
  ],
  [BlockTypeEnum.DATA_EXPORTER]: [
    DataSourceTypeEnum.GENERIC,
    DataSourceTypeEnum.FILE,
    DataSourceTypeEnum.S3,
    DataSourceTypeEnum.MYSQL,
    DataSourceTypeEnum.POSTGRES,
  ],
  [BlockTypeEnum.TRANSFORMER]: [
    DataSourceTypeEnum.POSTGRES,
  ],
  [BlockTypeEnum.SENSOR]: [
    DataSourceTypeEnum.GENERIC,
    DataSourceTypeEnum.S3,
    DataSourceTypeEnum.MYSQL,
    DataSourceTypeEnum.POSTGRES,
  ],
};

export default DataSourceTypeEnum;
