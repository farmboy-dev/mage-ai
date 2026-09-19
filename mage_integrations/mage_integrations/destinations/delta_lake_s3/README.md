# Delta Lake S3

Write Delta tables to S3-compatible storage, including MinIO and Ceph. The connector uses the public deltalake 0.20.2 writer API.

| Key | Description | Default |
| --- | --- | --- |
| `aws_access_key_id` | Storage access key ID. | Required |
| `aws_secret_access_key` | Storage secret access key. | Required |
| `aws_session_token` | Optional temporary session token. | `null` |
| `aws_region` | Signing region for both storage clients. | `us-west-2` |
| `aws_endpoint` | Full S3-compatible endpoint URL. | `null` |
| `aws_s3_addressing_style` | `path` or `virtual`. Use `path` for typical MinIO/Ceph deployments. | `path` |
| `aws_allow_http` | Explicitly permit an HTTP endpoint; does not disable HTTPS certificate verification. | `false` |
| `bucket` | Existing destination bucket. | Required |
| `object_key_path` | Prefix inside the bucket, without the bucket or table name. May be empty. | Empty |
| `table` | Table name/path appended to the prefix. | Required |
| `mode` | `append`, `overwrite`, `ignore`, or `error`. | `append` |

Configure partition columns through the stream's partition settings. Both boto3 and delta-rs receive the endpoint, credentials, region, and addressing configuration.

## Write behavior

- `append` preserves existing records and rejects incompatible schemas.
- `overwrite` replaces all rows for an unpartitioned table. For a partitioned table, it replaces only the partition combinations present in the incoming batch. Other partitions remain intact.
- `ignore` leaves an existing table unchanged; `error` fails if a table already exists.
- An empty batch does not change the table.
- Delta commits use the SDK transaction API. Previously committed log files are never rewritten by this connector.
- Existing files without a Delta log cause an error. Choose an empty table path; the connector will not delete those files.
- Authentication and storage errors propagate; they are not interpreted as missing tables.

Nullable scalar values retain their declared types. Boolean `false` remains false. Objects are serialized as JSON strings and arrays retain a list of string elements. Invalid values fail instead of silently changing a column's type. Partition overwrite with double quotes in column names is rejected because of the installed SDK's predicate handling; apostrophes in partition values and null values are supported.

## Internal endpoint example

```json
{
  "aws_access_key_id": "<access-key>",
  "aws_secret_access_key": "<secret-key>",
  "aws_region": "us-east-1",
  "aws_endpoint": "https://minio.internal:9000",
  "aws_s3_addressing_style": "path",
  "aws_allow_http": false,
  "bucket": "analytics",
  "object_key_path": "delta",
  "table": "events",
  "mode": "append"
}
```

For a local HTTP test server, set `aws_allow_http` to the JSON boolean `true` explicitly. Use trusted certificates for HTTPS endpoints.

This connector retains `AWS_S3_ALLOW_UNSAFE_RENAME=true` and does not configure a distributed locking provider. Use a single writer per table; concurrent writers are not validated by this integration. Tests against MinIO do not establish compatibility with every Ceph deployment.
