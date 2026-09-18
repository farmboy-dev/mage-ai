# 삭제 기능 호환 코드 조사 목록

2026-09-18. 체크포인트 `d0d25e265` 기준. 아래 목록은 감사 기록이며 향후 런타임 차단 목록으로 사용하지 않는다.

## REMOVED_EXECUTOR_TYPES — 4개

- `azure_container_instance`
- `ecs`
- `gcp_cloud_run`
- `pyspark`

## REMOVED_PROJECT_CONFIGS — 4개

- `azure_container_instance_config`
- `ecs_config`
- `emr_config`
- `gcp_cloud_run_config`

## REMOVED_CONNECTORS — 42개

- `airtable`
- `algolia`
- `amazon_sqs`
- `amplitude`
- `azure_blob_storage`
- `azure_data_lake`
- `azure_event_hub`
- `bigquery`
- `chargebee`
- `commercetools`
- `datadog`
- `delta_lake_azure`
- `dynamodb`
- `facebook_ads`
- `freshdesk`
- `front`
- `google_ads`
- `google_analytics`
- `google_cloud_pubsub`
- `google_cloud_storage`
- `google_search_console`
- `google_sheets`
- `hubspot`
- `intercom`
- `kinesis`
- `knowi`
- `linkedin_ads`
- `mode`
- `monday`
- `outreach`
- `paystack`
- `pipedrive`
- `postmark`
- `powerbi`
- `redshift`
- `salesforce`
- `snowflake`
- `stripe`
- `tableau`
- `teradata`
- `twitter_ads`
- `zendesk`

## cloud_features 직접 참조 파일

- `mage_ai/api/resources/BlockResource.py`
- `mage_ai/api/resources/PipelineResource.py`
- `mage_ai/data_preparation/executors/executor_factory.py`
- `mage_ai/data_preparation/executors/streaming_pipeline_executor.py`
- `mage_ai/data_preparation/models/block/__init__.py`
- `mage_ai/data_preparation/models/block/data_integration/utils.py`
- `mage_ai/data_preparation/models/block/sql/__init__.py`
- `mage_ai/data_preparation/models/pipelines/integration_pipeline.py`
- `mage_ai/data_preparation/repo_manager.py`
- `mage_ai/data_preparation/templates/template.py`
- `mage_ai/server/api/integration_sources.py`
- `mage_ai/services/search/block_action_objects.py`
- `mage_ai/streaming/sinks/generic_io.py`
- `mage_ai/streaming/sinks/sink_factory.py`
- `mage_ai/streaming/sources/source_factory.py`
- `mage_ai/tests/data_preparation/executors/test_cloud_removed.py`
- `mage_ai/tests/data_preparation/test_cloud_connectors_removed.py`

## 목록 밖에 남은 오류 전용 경로

| 파일 | 남은 동작 |
|---|---|
| `mage_ai/api/resources/RemovedCloudResource.py` 및 Cluster/ComputeCluster/ComputeConnection/ComputeServiceResource | 4개 API resource에서 제거 안내만 반환 |
| `mage_ai/cli/main.py` | create_spark_cluster 명령과 EMR 경로 기본 인자 |
| `mage_ai/io/config.py` | AWSSecretLoader 생성 시 제거 오류 |
| `mage_ai/data_preparation/shared/utils.py` | azure_secret_var 호출 시 제거 오류 |
| `mage_ai/orchestration/db/setup.py`, `orchestration/constants.py` | AWS_DB_SECRETS_NAME / AZURE_SECRET_DB_CONN_URL 분기·식별자 |
| `mage_ai/data_preparation/variable_manager.py` | gs:// 경로만 특별 거절 |
| `mage_ai/data_preparation/logging/logger_manager_factory.py` | gcs 로그 타입만 특별 거절 |
| `mage_ai/cluster_manager/manage.py`, `cluster_manager/workspace/base.py` | 비-Kubernetes workspace 거절 문구 |

## 지원 식별자와 분리해야 할 이름

`ExecutorType.PYSPARK`는 과거 EMR 실행기 식별자지만 `PipelineType.PYSPARK`, PySpark kernel, spark_config는 유지 대상이다. 이 문자열을 전역 치환하거나 이름 검색 결과를 일괄 삭제하지 않는다. S3용 boto3/botocore 및 AWS 자격증명 필드도 유지한다.
