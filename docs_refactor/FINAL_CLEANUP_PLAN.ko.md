# 최종 잔여 코드 정리 변경안 — R1 적용 완료

2026-09-18. C2e 및 Tableau·Teradata 완료분을 `d0d25e265`로 로컬 커밋했다. GitHub push는 하지 않았다. 최초 조사 시에는 문서만 추가했다. 이후 사용자 승인으로 R1을 적용했다. [R1 적용 결과](FINAL_CLEANUP_R1_RESULT.ko.md)를 참고한다.

[실제 제거 식별자 전체 목록](REMOVED_FEATURES_INVENTORY.ko.md): connector 42개, executor 4개, project config 4개와 별도 API·Secrets·CLI 호환 경로.

## 목표

삭제한 공급자 이름을 기억하는 런타임 코드·전용 API·설정 식별자를 없앤다. 남길 기능의 등록 정보가 검증 기준이 되도록 바꾼다. 임의 HTTP 요청 자체를 보내지 못하게 하는 것이 아니라, 전용 기능이 없고 공통 API도 지원하지 않는 값을 실행하지 못하는 상태로 만든다.

이전 단계의 데이터 이관 안내는 docs_refactor에 남기고, 런타임은 일반 `Unsupported connector`, `Unsupported executor`, `Unsupported storage scheme` 오류만 반환한다. 예전 기능명을 열거하는 테스트 대신 임의의 미등록 식별자·유효한 기능의 정상 동작을 검증한다.

## R1 — 승인 후 적용한 범위

### 1. 공통 API를 지원 목록 기준으로 전환

`mage_ai/shared/cloud_features.py`를 제거하고 신규 `mage_ai/shared/supported_features.py`에 지원 기능 검증을 둔다. 목록은 임의 import를 수행한 결과가 아니라 현재의 source/destination 등록, SQL provider 등록, streaming factory 지원 타입, 기본 템플릿 등록을 기준으로 한다. 기존 카탈로그를 재사용하고 중복된 거대 목록을 만들지 않는다. import 순환을 피하도록 등록/검증의 의존 방향을 분리한다.

하나의 전체 합집합으로 검증하지 않고 다음 문맥을 구분한다.

- integration source 및 destination: 각 방향의 현재 카탈로그.
- SQL data_provider: 실제 지원 SQL provider.
- streaming connector_type: source/sink 방향별 지원 목록.
- 기본 data_source/template_path: pipeline 언어·블록 종류에 맞는 기본 템플릿. s3/amazon_s3 같은 기존 정상 식별자 구분 보존.
- custom template·사용자 Python 코드·일반 name/content: 기본 커넥터 ID로 잘못 판단하지 않음.
- 기본 템플릿 검색 캐시: 현재 등록된 기본 템플릿만 허용. 사용자 블록·사용자 템플릿은 이름으로 삭제하지 않음.

수정 파일:

- `mage_ai/api/resources/BlockResource.py`, `PipelineResource.py`
- `mage_ai/data_preparation/models/block/__init__.py`
- `mage_ai/data_preparation/models/block/data_integration/utils.py`
- `mage_ai/data_preparation/models/block/sql/__init__.py`
- `mage_ai/data_preparation/models/pipelines/integration_pipeline.py`
- `mage_ai/data_preparation/templates/template.py`, `templates/constants.py`
- `mage_ai/server/api/integration_sources.py`
- `mage_ai/services/search/block_action_objects.py`
- `mage_ai/streaming/sources/source_factory.py`, `sinks/sink_factory.py`, `sinks/generic_io.py`
- `mage_ai/streaming/constants.py`
- `mage_ai/data_preparation/executors/streaming_pipeline_executor.py`
- 각 provider 등록의 단일 근거가 필요한 `mage_ai/data_integrations/{sources,destinations}/constants.py`, `mage_ai/api/resources/DataProviderResource.py`

동적 import 앞에서 검증한다. 스트리밍은 현재와 같이 source 초기화 전에 모든 YAML source/sink를 검사한다. API 오류의 일반 문구 전환과 HTTP 상태 변경을 혼동하지 않으며 기존 공통 API의 응답 규약은 유지한다.

### 2. 오류만 반환하는 전용 API 제거

삭제할 전용 파일 13개:

- `mage_ai/api/resources/RemovedCloudResource.py`
- `mage_ai/api/resources/ClusterResource.py`
- `mage_ai/api/policies/ClusterPolicy.py`
- `mage_ai/api/presenters/ClusterPresenter.py`
- `mage_ai/api/resources/ComputeClusterResource.py`
- `mage_ai/api/policies/ComputeClusterPolicy.py`
- `mage_ai/api/presenters/ComputeClusterPresenter.py`
- `mage_ai/api/resources/ComputeConnectionResource.py`
- `mage_ai/api/policies/ComputeConnectionPolicy.py`
- `mage_ai/api/presenters/ComputeConnectionPresenter.py`
- `mage_ai/api/resources/ComputeServiceResource.py`
- `mage_ai/api/policies/ComputeServicePolicy.py`
- `mage_ai/api/presenters/ComputeServicePresenter.py`

`mage_ai/frontend/api/index.ts`의 CLUSTERS/COMPUTE_CLUSTERS/COMPUTE_CONNECTIONS/COMPUTE_SERVICES 선언·등록도 제거한다.

현재 서버는 `/api/<resource>` 공통 정규식으로 요청을 받고 `api/operations/base.py`에서 resource 클래스를 동적으로 import한다. 파일 삭제만으로 404가 보장되지 않는다. `mage_ai/server/api/base.py`와 `mage_ai/api/operations/base.py`에서 존재하는 resource 이름만 해석하고 미등록 resource·parent·child는 일반 HTTP 404로 처리하도록 정리한다. 특정 삭제 이름을 차단하는 새 목록은 만들지 않는다. 리소스 내부 의존성 ImportError까지 404로 숨기지 않으며 인증·권한 검증은 유지한다.

검증 URL: `/api/clusters`, `/api/compute_clusters`, `/api/compute_connections`, `/api/compute_services`의 collection/member/nested 및 GET/POST/PUT/DELETE. 임의 미등록 이름도 검사한다. **Spark 설정 UI, 내부 kernel, /compute 페이지는 삭제 대상이 아니다.**

### 3. 실행기·설정·Secrets 호환 코드

아래 경로는 `mage_ai/` 기준이다.

| 파일 | 변경 |
|---|---|
| `data_preparation/models/constants.py`, `frontend/interfaces/ExecutorType.ts` | executor enum을 local_python/local_python_force/k8s로 축소. PipelineType.PYSPARK·kernel·spark_config 유지 |
| `data_preparation/executors/executor_factory.py` | 지원 executor만 허용. 설정 누락의 기본값과 명시적인 잘못된 값의 오류를 구분 |
| `data_preparation/repo_manager.py`, `api/resources/ProjectResource.py` | 제거된 config 이름별 검사 대신 지원 프로젝트 설정 기준 검증. 사용자 확장 설정 계약을 확인하여 임의 폐쇄하지 않음. 프로젝트 파일 자동 덮어쓰기 금지 |
| `cli/main.py` | create_spark_cluster 명령과 전용 기본 인자 제거. 실제 PySpark kernel 유지 |
| `io/config.py` | AWSSecretLoader 호환 클래스와 삭제 공급자의 미사용 ConfigKey·VerboseConfigKey·매핑 제거 |
| `data_preparation/shared/utils.py` | azure_secret_var 함수·등록 제거. env_var·mage_secret_var 유지 |
| `orchestration/db/setup.py`, `orchestration/constants.py` | AWS_DB_SECRETS_NAME/AZURE_SECRET_DB_CONN_URL 분기·상수 제거. 직접 DB URL·DB_* 설정 유지 |
| `data_preparation/variable_manager.py`, `settings/repo.py`, `shared/constants.py` | gs:// 특별 거절 대신 로컬·s3 저장 경로만 허용. 디렉터리 생성 전에 URI scheme 검증 |
| `data_preparation/logging/logger_manager_factory.py` | file/s3만 선택 가능. 잘못된 명시적 값의 file fallback 방지 |
| `cluster_manager/manage.py`, `cluster_manager/workspace/base.py`, `cluster_manager/constants.py` | K8S 지원 기준 일반 오류 및 미사용 클라우드 식별자 정리. 실제 K8S annotation 참조는 별도 분류 |
| `io/base.py`, `frontend/interfaces/DataSourceType.ts`, `frontend/interfaces/IntegrationSourceType.ts`, `streaming/constants.py` | 삭제 공급자의 미사용 enum 제거 |
| `frontend/components/v2/Apps/Browser/System/mocks.ts` | 삭제 전용 모듈을 가리키는 가상 파일 경로 정리 |

공통 설정의 활성 사용처가 발견되면 일괄 삭제하지 않고 별도 범위를 보고한다. `pyspark`, AWS 자격증명 등 보존 기능과 이름을 공유하는 문자열을 전역 치환하지 않는다.

### 4. 테스트 전환

`test_cloud_connectors_removed.py`, `test_cloud_runtime_removed.py`, `executors/test_cloud_removed.py`, `executors/test_cloud_streaming_removed.py`, `test_templates.py`의 제거 목록 기반 검증을 임의 미등록 값·방향별 지원 목록·일반 오류 검증으로 전환한다. 삭제 API의 404 회귀는 유지한다. 신규 `mage_ai/tests/api/test_supported_resources.py`에서 404·권한·기존 API 응답을 검증한다. 기본/custom template·사용자 블록 검색·로컬/S3·내부 Secrets·K8S·PySpark 보존을 확인한다.

## R2 — 의존성·이미지 정리, R1 뒤 별도 승인

대상 파일: `requirements.txt`, `setup.py`의 개별 extra와 all, `mage_integrations/requirements.txt`, `Dockerfile`, `dev.Dockerfile`. dev backend는 runtime 이미지를 상속하므로 선언 삭제만으로 설치 패키지가 사라지지 않는다.

| 후보 | 조사 결과 및 조건 |
|---|---|
| Google Ads/Analytics/API/BigQuery/Storage/PubSub/Run/IAM SDK, gspread | requirements·extras에 남은 선언 정리 후보. 잔여 import 및 동적 로딩 검증 필요 |
| Azure EventHub/Identity/KeyVault/ContainerInstance/Blob SDK | 클라우드 구현·dbt 어댑터 의존 관계를 함께 확인 |
| Snowflake·Redshift connector, Facebook SDK, simple_salesforce, stripe, twitter-ads, zenpy, teradatasql | 삭제 구현 전용 의존 선언 정리 후보 |
| dbt-bigquery, dbt-redshift, dbt-snowflake, dbt-synapse | 전용 profile/template 분기와 함께 정리. 내부 dbt 어댑터 보존 |
| Dockerfile sparkmagic/Livy 설치·원격 설정 다운로드 | 현재 로컬 PySpark kernel과 분리 검증 후 정리 후보. Java/PySpark 지원 삭제를 의미하지 않음 |

boto3/botocore, openai, requests/httpx, Singer, pyarrow, deltalake, 내부 DB 드라이버 및 내부 dbt 어댑터는 유지한다. oscrypto와 Git 기반 빌드 설치는 실제 사용처·resolver 결과를 확인한 뒤 판단한다. 현재 실행 이미지에서 수동 uninstall하지 않는다.

Datadog metrics, Hugging Face AI, Google Chat 등은 아직 실제 구현이 남아 있어 오류 전용 호환 코드와 구분한다. 해당 기능·UI·설정 제거는 별도 변경안을 먼저 작성한다. 이번 목록만으로 모든 외부 연결 제거 완료라고 보고하지 않는다.

검증: 새 이미지 빌드, pip check, 설치 목록·용량 비교, core import, S3/AI/내부 DB/Spark 회귀, UI smoke. 빌드 시 네트워크 의존 완전 제거는 별도 작업이다.

## R3 — 보존 기능 호환성, 별도 승인

Couchbase의 libssl.so.1.1 누락과 Delta Lake writer의 PyDeltaTableError import 실패는 이전 커밋에서도 재현한 기존 문제다. 삭제 방식으로 해결하지 않는다.

후보 파일: Dockerfile/dev.Dockerfile, runtime requirements, `mage_integrations/mage_integrations/destinations/delta_lake/writer.py` 및 관련 tests. 설치 버전과 공식 지원 API를 대조해 SDK 버전 정합성 또는 adapter 수정을 선택한다. 구체적인 버전 변경은 R1 승인에 포함하지 않는다. 상세 API에서 두 보존 커넥터가 정상 제공되고 로컬 대체 저장소·schema 검증을 통과해야 완료다.

## 기존 설정의 의미 변화

- 과거 전용 API/CLI/모듈: 404, 명령 없음, ImportError 등 미존재 동작.
- 공통 API의 미등록 connector/executor/storage: 일반 오류. 공급자별 이전 안내는 문서에만 유지.
- azure_secret_var: 미등록 템플릿 함수로 실패. AWSSecretLoader: import 불가.
- 과거 클라우드 DB 환경변수: 더 이상 읽거나 특별 오류를 내지 않음. 기본 DB 설정으로 진행할 수 있어 배포 전에 직접 DB URL·DB_* 구성을 확인해야 함.
- 기존 프로젝트 파일은 자동 정리·이관하지 않음. 조회/수정에 영향을 주는 사례는 격리 fixture로 검사하고 보고.

## R1 완료 기준 및 승인 요청

1. 런타임 REMOVED_* 목록·공급자별 제거 안내·오류 전용 API/CLI/Secrets 코드 없음.
2. 미등록 요청이 SDK import·파일 생성·클라이언트 초기화 전에 일반 오류/404로 종료.
3. 정상 기본/custom template, source/destination 방향, 내부 기능 보존.
4. Python·TypeScript·API·UI·외부 연결 감사와 개발 서버 응답 확인. 기존 이미지 오류 2건은 별도 명시.
5. 역사적 docs_refactor 기록은 보존. 모든 파일에서 공급자 이름 문자열을 0개로 만드는 것이 목표는 아님.

**R1 코드·API·식별자·테스트 전환은 승인 후 적용했다. R2 이미지·패키지 변경과 R3 호환성 수정은 별도 변경안 승인 후 진행한다.** 추가 파일 수정이 필요하면 적용 전에 보고한다. 코드·주석·오류 메시지는 영어로 작성한다.
