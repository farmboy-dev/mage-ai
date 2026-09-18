# 남은 클라우드 커넥터·패키지 제거 계획 — 승인 전

상태 갱신: 이 계획 작성 후 사용자가 C1을 승인했고 구현을 완료했다. [C1 결과](CLOUD_CONNECTOR_C1_REMOVAL.ko.md)를 참고한다. 아래는 승인 당시의 계획이며 C2·C3는 미적용이다.

2026-09-18, 로컬 HEAD `1912c297f`와 현재 미커밋 수정 상태 기준. 사용자가 승인한 작업은 조사와 변경안 작성이다. 이번에는 소스·설정·의존성·컨테이너를 변경하지 않았다. 로컬 파일과 개발 컨테이너의 설치된 패키지 메타데이터를 읽었으며 외부 서비스 접속·키 입력·패키지 설치·이미지 빌드는 하지 않았다.

## 결론과 제안 순서

**C1: 여섯 공급자 커넥터와 모든 기본 진입점 제거 → C2: 나머지 클라우드 런타임 기능 정리 → C3: 의존 패키지·이미지 경량화** 순서를 권장한다. 단계별로 승인받는다. 메뉴 숨김만으로 기능이 제거되거나 SDK가 빠지는 것은 아니다.

현재 Dockerfile은 로컬 wheel의 `mage-ai[all]`과 `mage-integrations`를 함께 설치한다. 두 배포 패키지의 의존성과 dbt 어댑터를 모두 확인해야 SDK가 다시 설치되는 것을 막을 수 있다. 이번 조사로 이미지 감소 용량을 측정하지 않았으므로 절감 수치를 제시하지 않는다.

## 보존 조건

- S3/MinIO/Ceph: 일반 I/O, Data Integration source/destination, 센서, 스트리밍 sink, 중간 결과 저장, 로그, S3 기반 Delta Lake. `boto3`, `botocore` 및 필요한 S3 공통 의존성 유지.
- 내부 OpenAI 호환 AI와 `openai` SDK, base URL·모델 설정 유지.
- Python/PySpark 커널과 Spark 설정·SQL·DataFrame 처리 유지. PySpark는 클라우드 커넥터로 분류하지 않는다.
- 내부 HTTP API, 로컬 파일, 사내 DB, Kafka·RabbitMQ 등 내부 메시징 유지. `requests`, `httpx`, `pyarrow`, DB 드라이버를 공급자 SDK의 하위 의존성이라는 이유만으로 삭제하지 않는다.
- 로컬 dbt 실행과 내부 DB·Spark용 어댑터 유지. 클라우드 dbt 어댑터는 별도 제거 대상으로 구분.
- 사용자 프로젝트의 코드·파이프라인·자격증명·저장 데이터는 자동 삭제하거나 다른 공급자로 변환하지 않는다.
- Compute 서버 라우팅, Secrets UI, 이미 적용한 A+B 레이아웃은 이번 범위에서 제외한다.

## C1: 다음 구현 승인 요청 범위

대상은 **Azure Blob Storage, BigQuery, Google Cloud Storage, Google Sheets, Redshift, Snowflake**다. 전용 파일은 [81개 파일 목록](CLOUD_CONNECTOR_C1_FILES.ko.md)에 실제 경로로 열거했다. 공통 파일은 삭제하지 않고 아래 항목만 수정한다.

### 1. UI·카탈로그·템플릿

| 파일 | 제안 변경 | 사용자에게 보이는 결과 |
|---|---|---|
| `mage_ai/frontend/interfaces/DataSourceType.ts` | 여섯 공급자를 loader/exporter/transformer/sensor 표시 목록에서 제외 | 해당 기본 템플릿 선택지 제거, S3·내부 DB 유지 |
| `mage_ai/frontend/components/PipelineDetail/AddNewBlocks/utils.tsx` | 공통 메뉴와 스트리밍 목록의 해당 공급자 제거 | 기존·신형 블록 추가 UI 모두 반영 |
| `mage_ai/frontend/interfaces/DataProviderType.ts` | BigQuery·Redshift·Snowflake 선택 정의와 참조 정리 | SQL 공급자 표시 일관성 유지 |
| `mage_ai/frontend/interfaces/IntegrationSourceType.ts` | 제거된 integration 공급자 전용 분기·선택 정의 정리 | integration 관련 화면이 삭제된 공급자를 가정하지 않음 |
| `mage_ai/api/resources/DataProviderResource.py` | BigQuery·Redshift·Snowflake를 API 반환 목록에서 제외 | SQL 공급자 드롭다운의 실제 데이터 원본 정리 |
| `mage_ai/data_preparation/templates/constants.py` | 해당 기본 템플릿 및 Azure/GCS Delta Lake 템플릿 등록 제거 | Browse templates 경로에서도 표시되지 않음 |
| `mage_ai/data_integrations/sources/constants.py`, `destinations/constants.py` | SQL_SOURCES·SOURCES·DESTINATIONS에서 대상 공급자 및 Delta Lake Azure 제외 | integration 선택·자동 생성 템플릿에서도 제외 |
| `mage_ai/data_preparation/templates/repo/io_config.yaml` | 신규 프로젝트의 제거 공급자 전용 예시 설정 정리 | 새 프로젝트 설정 파일에서 미지원 기능 안내 제거 |

신형 UI `AddNewBlocks/v2/ButtonItems.tsx`도 공통 `getdataSourceMenuItems`를 호출한다. 개별 JSX를 일괄 삭제하는 대신 공통 목록을 정리하고 v1/v2를 함께 검증한다. `BlockTemplateResource.py`는 TEMPLATES 및 integration 카탈로그를 사용하므로 목록과 직접 UUID 조회가 함께 정리되는지 검사한다. 일반 코드 에디터나 블록 종류 자체는 제거하지 않는다.

### 2. 실제 구현과 연결 분기

| 파일·범위 | 제안 변경 |
|---|---|
| `mage_ai/io/{azure_blob_storage,bigquery,google_cloud_storage,google_sheets,redshift,snowflake}.py` | 전용 구현 제거 |
| `mage_ai/data_preparation/models/block/sql/{bigquery,redshift,snowflake}.py` | 전용 SQL 보조 구현 제거 |
| `mage_ai/data_preparation/models/block/sql/__init__.py` | 세 공급자 import·실행 분기 제거. 다른 SQL 공급자와 Spark 분기 유지 |
| `mage_ai/data_preparation/templates/{data_loaders,data_exporters,sensors}/`의 대상 파일 | 전용 템플릿 제거. 정확한 파일은 81개 목록 참조 |
| `mage_integrations/mage_integrations/{sources,destinations,connections}/`의 대상 디렉터리 | 실제 존재하는 전용 구현·설정 템플릿·README·스키마 제거. `delta_lake_azure` 포함. 공통 base·SQL·S3 코드는 유지 |
| `mage_ai/streaming/constants.py`, `sinks/generic_io.py`, `sinks/sink_factory.py` | BigQuery·Redshift·Snowflake의 GenericIO 경로와 GCS 전용 sink 선택 제거 |
| `mage_ai/streaming/sinks/google_cloud_storage.py` | GCS 전용 sink 제거 |
| `mage_ai/io/base.py`, `io/config.py` | 삭제된 구현 참조를 정리. 기존 설정 식별 및 명시적 오류에 필요한 식별자는 남길 수 있으나 활성 목록에는 노출하지 않음. Google/Azure 공통 설정은 C2 사용처가 남아 있으므로 통째로 삭제하지 않음 |

같은 공급자의 스트리밍 sink를 C1에 포함하는 이유는 I/O 모듈을 삭제하면서 그 모듈을 동적으로 import하는 경로를 남기면 실행 시 깨지기 때문이다. Event Hub·PubSub·Kinesis 등 별도 구현은 C2로 분리한다.

### 3. 기존 파이프라인과 직접 API 요청

- 제거된 `data_source`, SQL `data_provider`, integration UUID, streaming `connector_type`를 사용하는 기본 실행 경로는 **실제 import·연결 전에 “이 사내 배포에서 제거된 커넥터”라는 오류**를 반환하도록 한다.
- 검증 후보: 기존 `mage_ai/shared/cloud_features.py`에 제거 대상 식별·검증 추가, `api/resources/BlockResource.py`의 생성·수정, `data_preparation/models/block/__init__.py`·`block/sql/__init__.py`의 실행, `block/data_integration/`·`models/pipelines/integration_pipeline.py`의 integration 진입, `server/api/integration_sources.py`의 동적 모듈 로딩, source/destination API 직접 조회, streaming sink factory.
- 기존 파이프라인의 읽기·편집까지 막지 않고, 가능한 한 해당 블록의 생성·변경·실행에서 문제를 식별한다. 저장된 YAML과 Python 코드를 자동 변경하지 않는다.
- 사용자가 Python 코드에서 삭제된 `mage_ai.io.*`를 직접 import하면 ImportError가 날 수 있다. 임의 Python 코드를 분석해 자동 변환하거나 모든 네트워크 접근을 차단하는 작업은 포함하지 않는다. 마이그레이션 문서에 이 제한을 명시한다.
- 인증키 값은 오류나 보고서에 포함하지 않는다. 기존 자격증명은 자동 삭제하지 않고 미사용 상태로 남긴다.

### 4. C1 검증·테스트 수정 계획

- `mage_ai/tests/data_preparation/test_templates.py`: 제거 대상 템플릿 기대값을 비노출·미지원 오류 검증으로 변경하고 내부 커넥터 템플릿 검증 유지.
- `mage_ai/tests/streaming/sinks/test_generic_io.py`: 클라우드 세 공급자 대신 유지 공급자와 제거 대상 오류 확인. `tests/io/create_table/test_bigquery.py` 같은 삭제 구현 전용 테스트 정리.
- API 템플릿·SQL 공급자·integration 카탈로그에서 대상이 빠지는지, 직접 식별자를 요청해도 import·네트워크 호출 전에 실패하는지 확인.
- 로컬 파일·내부 DB용 SQL 분기 import, S3 호환·내부 AI 기존 회귀 검증, PySpark 커널·Spark UI 기존 테스트.
- 격리된 테스트 프로젝트에서 기존 UI와 신형 UI를 모두 검증. loader/exporter/transformer/sensor, Browse templates, SQL 공급자, integration, streaming 메뉴 확인. 실제 사용자 프로젝트의 기능 플래그를 변경하지 않음.
- 전체 TypeScript 검사. 기존 제거 커넥터가 설정된 테스트 파이프라인의 조회·편집 가능 여부 및 실행 오류 확인.

**C1에서는 SDK 패키지를 일괄 제거하지 않는다.** GCS 로그·저장, Azure Key Vault, Google SaaS, 클라우드 dbt 어댑터 등의 사용처가 남아 있기 때문이다. 이 단계만으로 이미지 경량화가 완료됐다고 보고하지 않는다.

## C2: 다음 승인 대상으로 분리할 런타임 기능

### 우선순위 갱신: C2a Algolia·Airtable

사용자 확인 요청에 따라 **Algolia와 Airtable을 외부 SaaS 제거 대상으로 명시**한다. C1에 남아 있던 이유는 내부망 서비스이기 때문이 아니라, C1을 여섯 공급자로 한정했기 때문이다. C2의 첫 작업으로 두 서비스의 I/O·기본 템플릿·Airtable integration·설정 예시 제거안을 준비한다. 현재 체크포인트를 커밋한 후 파일별 변경안과 검증 범위를 제출하고, 구현은 별도 승인 후 시작한다.

- Algolia: 호스팅 검색 SaaS이며 자체 서버 설치를 지원하지 않는다는 [공식 안내](https://support.algolia.com/hc/en-us/articles/4406975236625-Can-I-run-Algolia-on-premises-on-my-own-servers)를 확인했다.
- Airtable: AWS에 호스팅되는 클라우드 서비스라는 [공식 안내](https://www.airtable.com/company/data-residency-faqs)를 확인했다.
- 패키지는 사용처를 먼저 확인한다. `pyairtable`은 requirements 및 setup extras에 선언되어 있고, Algolia 구현은 `algoliasearch`를 import하지만 같은 선언 파일에서는 패키지 선언을 찾지 못했다. 현재 설치 여부와 공유 의존성을 확인한 뒤 정리 범위를 명시한다.
- 나머지 C2 기능·C3 SDK 전체 정리·Compute 배포 라우팅을 이 작업에 묶지 않는다.

| 대상 | 확인된 파일 | 변경 방향·보존 조건 |
|---|---|---|
| GCS 중간 결과 | `data_preparation/storage/gcs_storage.py`, `variable_manager.py`의 GCSVariableManager·factory 분기 | 제거 및 `gs://` 명시 오류. S3·로컬로 조용히 전환하지 않음. 기존 결과 이관은 별도 작업 |
| GCS 로그 | `data_preparation/logging/gcs_logger_manager.py`, `logger_manager_factory.py`, `logging/__init__.py` | GCS 타입·선택 제거. 기존 GCS 설정을 로컬 fallback으로 오인하지 않도록 오류 처리. 로컬·S3 유지 |
| Azure Key Vault | `services/azure/key_vault/`, `data_preparation/shared/utils.py`의 `azure_secret_var` | 별도 SDK 호출 제거. 로컬 `mage_secret_var`·환경변수 유지 |
| AWS Secrets Manager 잔여 구현 | `io/config.py`의 `AWSSecretLoader` | 이전 DB용 서비스 제거와 별개로 남아 있음. 내부 Python 참조 검색에서는 정의 외 사용처가 없지만 사용자 직접 import는 가능하므로 잔여 공개 구현 제거·이전 안내 후보 |
| Algolia·Airtable (C2a 우선) | `io/{algolia,airtable}.py`, 기본 loader/exporter 템플릿, Airtable integration source/destination/connection | 외부 SaaS 연결 제거 후보. 기본 메뉴·검색 캐시·설정·오류 처리 동시 정리 |
| 클라우드 스트리밍 | `streaming/sources/{amazon_sqs,kinesis,google_cloud_pubsub,azure_event_hub}.py`, `sinks/{kinesis,google_cloud_pubsub,azure_data_lake}.py`, 각 factory·constants·YAML·UI | 해당 공급자 제거. S3·Kafka·내부 메시징 유지 |
| 기타 클라우드·SaaS | Google Ads/Analytics/Search Console, DynamoDB, Airtable 등 integration 카탈로그의 나머지 외부 서비스 | C1 여섯 공급자와 별개. 전체 목록과 공유 사용처를 조사해 추가 변경안 제출 |

위 경로는 `mage_ai/` 기준이며 integration은 `mage_integrations/`에 있다. C2는 현재 즉시 적용 승인을 요청하는 범위가 아니다.

## C3: 의존 패키지 정리 계획

### 변경 파일

- `requirements.txt`: runtime/extras 선언, 중복 `redshift-connector` 등 함께 정리.
- `setup.py`: 개별 extras와 `all` 양쪽 정리. `[all]`에서 재도입되지 않도록 한다.
- `mage_integrations/requirements.txt`: 설치 시 필수로 읽히는 공급자 SDK 정리. 해당 `setup.py`는 이 파일을 읽으므로 별도 하드코딩을 추가하지 않는다.
- `Dockerfile`: 전용 공급자 때문에 설치한 항목만 참조 확인 후 정리. S3·내부 DB·R·로컬 dbt까지 일괄 축소하지 않는다.
- 개발 이미지는 기존 base에 패키지가 남아 있을 수 있으므로 새 의존성 기준으로 이미지 재빌드·검증 후 교체한다. 현재 실행 중인 환경의 패키지를 수동 uninstall하지 않는다.
- 루트 `pyproject.toml`과 `poetry.lock`은 현재 DevEx 도구용이며 Docker runtime 의존성의 주 소스가 아니다. 클라우드 이름이 있다는 이유로 lock 전체를 임의 재생성하지 않는다.

### 패키지별 판단

| 후보 | 제거 조건 / 공유 사용처 |
|---|---|
| `google-cloud-bigquery`, `google-cloud-bigquery-storage`, `snowflake-connector-python`, `redshift-connector` | I/O·integration·streaming 참조와 관련 dbt 어댑터 정리가 선행되어야 함 |
| `google-cloud-storage` | 위 항목 외 GCS 로그·중간 결과·PubSub 관련 경로와 dbt 사용처 확인 필요 |
| `google-api-python-client`, `google-api-core`, Google 인증 관련 패키지, `gspread` | Sheets 외 Ads·Analytics·Search Console 등 사용처 구분. Google SDK를 이름만 보고 일괄 삭제하지 않음 |
| `azure-storage-blob`, `azure-eventhub`, `azure-identity`, `azure-keyvault-*` | Blob·Delta Lake·Event Hub·Key Vault·dbt Azure 어댑터 사용처 정리 후 제거 |
| `dbt-bigquery`, `dbt-redshift`, `dbt-snowflake`, `dbt-synapse` | 클라우드 전용 어댑터 제거 후보. `dbt-core`, Spark·내부 DB용 어댑터 유지 |
| `google-cloud-run`, `google-cloud-iam`, `azure-mgmt-containerinstance`, `azure-keyvault-certificates` | 실행 코드 제거 이후 패키지 선언에 남은 후보. 현재 Python import 검색에서 직접 사용처를 찾지 못했지만 동적 로딩·설치 의존성 검증 후 제거 |
| `boto3`, `botocore`, S3 관련 공통 의존성 | **유지**. S3/MinIO/Ceph 사용 |
| `openai`, `pyarrow`, `deltalake`, `requests`, `httpx`, DB 드라이버 | **공통 보존 대상**. 공급자 삭제의 연쇄 삭제 대상으로 취급하지 않음 |

개발 컨테이너의 설치 메타데이터에서도 dbt-bigquery→Google SDK, dbt-snowflake→Snowflake connector, dbt-redshift→Redshift connector, dbt-fabric→azure-identity 의존을 확인했다. Great Expectations·Delta Lake 등에는 선택적 의존 선언도 있다. 이는 설치된 현재 환경의 선언 관계이며, C3 이후 resolver 결과를 예측한 확정 목록이 아니다.

C3 검증은 깨끗한 이미지 빌드, `pip check`, 핵심 모듈 import, S3·AI·내부 SQL·Spark 회귀, UI smoke, 실제 설치 패키지 목록 및 이미지 크기 비교다. Sparkmagic/Java/PySpark 구성과 빌드 시 인터넷 의존 제거는 별도 승인 대상으로 두며, 이번 계획을 이유로 PySpark 기능을 다시 제거하지 않는다.

## 승인 요청

다음 구현은 **C1 전체: 여섯 공급자의 기본 UI·카탈로그·템플릿·I/O·SQL·integration·연계 streaming 경로 제거, 기존 설정에 대한 오류 처리와 회귀 검증**을 제안한다. 81개 전용 파일 외 공통 파일은 위 표대로 필요한 분기만 수정한다. C2·C3와 이미지 교체는 이후 별도 승인받는다.
