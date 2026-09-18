# Mage 사내망용 경량화 분석

분석 기준: 로컬 checkout `1912c297f` (2026-09-11), 분석일 2026-09-17.
대상 upstream: https://github.com/mage-ai/mage-ai/
아래 판단은 로컬 소스 정적 분석 결과이며, 실제 네트워크 캡처·오프라인 실행·이미지 크기 측정은 수행하지 않았다. 기능 코드는 변경하지 않았다.

**권장 방향:** Python/SQL 파이프라인 편집·실행·스케줄링·로그·로컬 저장·사내 DB 연결을 중심으로 구성하고, 퍼블릭 클라우드 및 SaaS 공급자별 구현을 제거한다. 내부망 네트워크 연결은 허용하는 것으로 가정한다. 추가 요구에 따라 **MinIO/Ceph용 S3 호환 기능과 사내 OpenAI 호환 AI 기능은 유지**한다. 퍼블릭 클라우드 관리 기능과 외부 서비스 전용 연동은 제거한다.

## 1. 우선 제거할 기능

표의 경로는 저장소 루트 기준이다. 디렉터리는 관련 구현 위치이며, 하위 공통 코드까지 일괄 삭제하라는 의미는 아니다.

| 영역 | 제거 후보 및 주요 경로 | 영향과 함께 정리할 부분 |
|---|---|---|
| AWS 실행·관리 | `mage_ai/services/aws/`, `services/compute/aws/`, `cluster_manager/aws/`, `data_preparation/executors/ecs_*`, `pyspark_*` | ECS, EMR, AWS 이벤트 관리 제거. `services/aws/s3/` 및 S3 공통 코드 보존. 실행기 factory·enum·Compute API·UI·프로젝트 설정에서 선택지를 함께 제거 |
| GCP 실행·관리 | `mage_ai/services/gcp/`, `cluster_manager/gcp/`, `data_preparation/executors/gcp_cloud_run_block_executor.py` | Cloud Run 실행과 관리 제거. 공통 클러스터 관리/Kubernetes까지 삭제하지 않음 |
| Azure 실행·관리 | `mage_ai/services/azure/`, `data_preparation/executors/azure_container_instance_executor.py` | Container Instances, Key Vault 기능 제거 |
| 클라우드 I/O | `mage_ai/io/{bigquery,google_cloud_storage,google_sheets,azure_blob_storage,redshift,snowflake,backblaze_b2}.py` | 공급자별 SQL 분기, `DataSource`, 설정 키, loader/exporter 템플릿, UI 선택지 동시 정리. S3는 MinIO/Ceph용으로 유지 |
| SaaS I/O | `mage_ai/io/{airtable,algolia}.py` | Airtable, Algolia 연결 제거 |
| 중간 결과 원격 저장 | `mage_ai/data_preparation/storage/gcs_storage.py` | GCS 선택 경로 제거. S3 저장과 `remote_variables_dir`는 유지하며 사내 endpoint 전달 보완. 기존 GCS 결과는 필요시 이관 |
| 원격 로그 | `mage_ai/data_preparation/logging/gcs_logger_manager.py` | GCS 로그 타입/설정 제거. 로컬 및 S3 호환 로그·조회 유지 |
| 외부 시크릿 | `services/aws/secrets_manager/`, `services/azure/key_vault/`, `mage_ai/io/config.py`의 AWS secret loader | `data_preparation/shared/utils.py`의 `aws_secret_var`·`azure_secret_var`도 제거. `mage_secret_var`·환경변수·로컬 암호화 시크릿 유지 |
| 클라우드 스트리밍 | `mage_ai/streaming/sources/{amazon_sqs,kinesis,google_cloud_pubsub,azure_event_hub}.py`, `sinks/{kinesis,google_cloud_pubsub,google_cloud_storage,azure_data_lake}.py` | SQS/Kinesis/PubSub/EventHub 및 해당 클라우드 sink 제거. S3 sink는 endpoint 설정을 보완하여 유지. source/sink factory·상수·YAML 템플릿·UI 정리 |
| 외부 서비스 작업 실행 | `mage_ai/services/{stitch,hightouch,metaplane,dbt}/` | Stitch/Hightouch/Metaplane/dbt Cloud 호출 제거. `services/dbt/`는 dbt Cloud API 구현이며 로컬 dbt 실행은 별도 기능 |
| 외부 알림 | `mage_ai/services/{slack,discord,teams,telegram,google_chat,opsgenie}/` | `orchestration/notification/{sender,config}.py`와 callback 템플릿 정리. 사내 SMTP 알림은 유지 가능 |
| AI 공급자 정리 | `mage_ai/ai/hugging_face_client.py` 및 공급자 선택 분기 | OpenAI 호환 방식으로 통일. AI API/UI, SDK, generator/wizard는 유지하고 endpoint·model 설정 보완. 별도 Hugging Face 프로토콜은 미사용 시 제거 |
| 벤더 서버 동기화 | `mage_ai/server/client/mage.py` | `backend.mage.ai/api/v1` 사용. `server/data/models.py` 호출부 확인 후 정리 |

**주의: `pyspark`라는 이름이 곧 온프레미스 구현을 뜻하지 않는다.**
`data_preparation/executors/pyspark_pipeline_executor.py`는 EMR 설정을 읽고, 실행 스크립트를 S3에 업로드한 뒤 EMR 작업을 제출한다. 사내 Spark를 유지하려면 이 경로를 그대로 보존할 수 없다. `services/spark/`, `io/spark.py`, 블록 Spark 기능과 EMR 실행기를 분리해야 한다.

## 2. Data Integration 커넥터 제거 목록

커넥터 구현은 `mage_integrations/mage_integrations/`에 있고, Mage의 카탈로그·실행 연결은 `mage_ai/data_integrations/`에 있다. 일반 Python 블록의 `mage_ai/io/`와 별도이므로 두 계층 모두 정리해야 한다.

**Source 우선 제거 후보** (`sources/` 하위 디렉터리):

- 클라우드 저장·DB: `azure_blob_storage`, `bigquery`, `dynamodb`, `google_cloud_storage`, `redshift`, `snowflake`.
- 광고·분석: `amplitude`, `datadog`, `facebook_ads`, `google_ads`, `google_analytics`, `google_search_console`, `linkedin_ads`, `twitter_ads`.
- SaaS 업무·결제: `airtable`, `chargebee`, `commercetools`, `freshdesk`, `front`, `google_sheets`, `hubspot`, `intercom`, `mode`, `monday`, `outreach`, `paystack`, `pipedrive`, `postmark`, `powerbi`, `salesforce`, `stripe`, `zendesk`.
- `github`는 퍼블릭 GitHub 연동 제거 대상으로 분류. 사내 GitHub Enterprise를 쓰면 해당 커넥터의 endpoint 지원을 별도로 확인.
- `titanic` 등 인터넷 데이터에 의존하는 샘플은 제거하거나 로컬 fixture로 전환.

**Destination 우선 제거 후보** (`destinations/` 하위 디렉터리):

- `airtable`, `bigquery`, `google_cloud_storage`, `redshift`, `salesforce`, `snowflake`, `delta_lake_azure`.
- Source/Destination의 `amazon_s3`는 유지. `delta_lake_s3`와 공통 `delta_lake`는 일괄 삭제에서 제외하고 실제 Delta Lake 사용 여부 및 endpoint 호환성을 별도 검토.

**내부망 용도로 보존 가능:** PostgreSQL, MySQL, MSSQL, Oracle, MongoDB, Couchbase, Doris, Dremio, Teradata, ClickHouse, Trino, Kafka, Elasticsearch/OpenSearch, SFTP, 일반 API/HTTP 커넥터. `tableau`는 코드에서 `base_url`을 설정받으므로 사내 Tableau Server 사용 여부에 따라 결정. `knowi`도 실제 배포 방식/endpoint 확인 후 결정한다.

등록부도 함께 수정해야 한다:

- `mage_ai/data_integrations/sources/constants.py`, `destinations/constants.py`
- `mage_ai/data_preparation/templates/data_integrations/`, loader/exporter 템플릿
- `mage_ai/frontend/interfaces/DataSourceType.ts` 및 Integration/SQL 설정 UI
- `mage_integrations/requirements.txt`, `mage_integrations/setup.py`

**패키지 전체 제거는 2차 선택지다.** Data Integration 파이프라인을 쓰지 않고 Python/SQL 블록만 쓸 경우 큰 축소 대상이지만, 일반 Block 모델이 `DataIntegrationMixin` 및 관련 유틸리티를 import한다. UI 숨김이나 패키지 삭제만으로 끝나지 않으며, Block 및 스케줄러 연결부터 분리해야 한다.

## 3. 클라우드 기능을 사용하지 않아도 확인해야 할 통신

| 경로 | 소스에서 확인한 동작 | 권장 조치 |
|---|---|---|
| `mage_ai/usage_statistics/` | `https://api.mage.ai/v1/usage_statistics`로 POST. 새 프로젝트 템플릿 `metadata.yaml`은 `help_improve_mage: true` | 전송 메서드를 no-op 처리한 뒤 호출부/API/UI를 단계적으로 제거. 기존 프로젝트 설정도 정리 |
| `usage_statistics/logger.py`의 `project_deny_improve_mage()` | 수집 거부 이벤트는 `override_validation=True`로 전송. `ProjectResource.py`에 설정 변경 시 호출 경로 존재 | 설정을 false로 바꾸는 것만으로 외부 통신 제거 완료로 판정하면 안 됨 |
| `api/resources/ProjectResource.py` | 프로젝트 응답 구성 시 PyPI의 `mage-ai/json`에서 최신 버전 조회. TTL 600초 캐시, timeout 3초 | 현재 fork 버전만 반환하거나 사내 릴리스 메타데이터로 전환 |
| `server/api/projects.py` | 별도의 PyPI 최신 버전 조회 구현 존재 | 신·구 API 양쪽 정리 |
| `server/scheduler_manager.py`, `orchestration/queue/process_queue.py` | Sentry/New Relic import 존재. 실제 초기화는 DSN/활성화 설정에 의존 | 외부 APM 미사용 시 초기화·decorator·예외 보고 호출을 제거한 후 SDK 삭제 |
| `services/datadog/`, `services/newrelic/` | 관측 연동 구현 | 외부 제공자를 제거하고 사내 로그/Prometheus/OTel 사용 여부에 맞춰 정리. 모든 환경에서 자동 전송된다는 뜻은 아님 |
| `frontend/pages/_app.tsx` | Google Analytics는 `isDemoApp`일 때만 렌더링 | demo 추적 분기와 불필요해진 `@next/third-parties` 제거 |
| OAuth 제공자 및 `api/resources/OauthResource.py` | Google/GitHub 등 공개 endpoint, 일부 fallback에 `api.mage.ai/v1/oauth/...` 사용 | 클라우드 로그인 및 벤더 중계 제거. 내부 OIDC/LDAP/GitLab/GHE는 callback과 endpoint를 내부 주소로 구성 |
| `scripts/run_app.sh` | 프로젝트 requirements가 있으면 시작할 때 `pip3 install -r` 실행 | 이미지 빌드 때 의존성 설치 완료. 시작 시 설치 제거 또는 사내 wheelhouse만 사용 |
| `data_preparation/git/__init__.py` | Git 작업 후 requirements 설치 경로 존재 | 사내 Git 동기화를 남길 때도 자동 pip 설치 동작을 함께 수정 |
| `scripts/install_other_dependencies.py` | `dbt deps` 실행 | 사내 패키지 저장소 사용 또는 빌드 때 패키지 포함 |

Monaco CodeEditor/CodeDiffEditor는 이미 `${getHost()}/monaco-editor/min/vs`의 로컬 자산을 사용한다. 소스 주석에 CDN 주소가 있다고 해서 실제 외부 CDN 요청으로 분류하지 않았다. 문서/프로모션 링크도 클릭 시 이동과 자동 요청을 구분해서 정리한다. 나머지 브라우저 요청과 서드파티 패키지 내부 통신은 실행 검증이 필요하다.

## 4. 의존성·이미지 경량화

**가장 먼저 고칠 빌드 파일은 `Dockerfile`이다.** 현재 기본 경로는 로컬 fork 소스를 설치하지 않고, 공개 PyPI의 `mage-ai[all]`과 공개 GitHub의 `mage-integrations`를 설치한다. `FEATURE_BRANCH` 경로 역시 `github.com/mage-ai/mage-ai`를 가리킨다. 로컬 파일을 수정해도 이미지의 실행 코드에 반영되지 않을 수 있다. fork 소스에서 만든 wheel과 사내 고정 의존성으로 설치하도록 바꾸어야 한다.

의존성 선언의 차이:

- `setup.py`의 기본 설치 의존성은 `requirements.txt`의 `# extras` 이전까지만 읽는다.
- `pip install -r requirements.txt`는 extras 이하까지 전부 설치한다.
- `mage-ai[all]`은 `setup.py`의 별도 전체 의존성 목록을 설치한다.
- `mage_integrations`는 별도 requirements를 설치하므로, 메인 패키지에서 지운 클라우드 SDK가 다시 들어올 수 있다.
- 현재 `pyproject.toml`은 주로 개발 도구 설정이다. 이것만 바꾸어 배포 의존성이 정리되지는 않는다.

| 패키지 그룹 | 제거/축소 후보 | 조건 |
|---|---|---|
| AWS | `aws-secretsmanager-caching`, `redshift-connector`, 미사용 `requests_aws4auth` | `boto3`, `botocore`와 필요한 전이 의존성은 MinIO/Ceph용으로 유지 |
| Google | `google-cloud-*`, `google-api-core`, `google-api-python-client`, `google-ads`, `google-analytics-data`, `gspread`, `db-dtypes` | 직접 의존성을 정리한 뒤 전이 의존성을 재해석. 공용 패키지를 이름만 보고 일괄 삭제하지 않음 |
| Azure | `azure-*` | Azure SDK 사용 경로 제거 후 |
| 클라우드 DW/dbt | `snowflake-connector-python`, `dbt-bigquery`, `dbt-redshift`, `dbt-snowflake`, `dbt-synapse` | `dbt-core`와 사내 DB용 adapter만 선택 설치 |
| SaaS | `pyairtable`, `facebook_business`, `simple_salesforce`, `stripe`, `twitter-ads`, `zenpy` | 대응 커넥터 제거 후 |
| AI | SDK 직접 호출로 통합한 뒤 미사용 `langchain`, `langchain_community` 축소 검토 | `openai` 유지. 현재 LangChain 사용 중이므로 리팩터링 전 삭제 불가. 보조 패키지도 잔여 import 확인 |
| 외부 APM | `datadog`, `newrelic`, `sentry-sdk` | 공통 실행 경로의 직접 import와 decorator를 먼저 제거 |
| 공개 Git API | `PyGithub` | GHE 포함 Git API 경로를 남기는지 확인. 일반 Git 동기화용 `GitPython`과 구분 |

추가 크기 축소 후보: 사용하지 않는 R 런타임과 패키지, Sparkmagic/Spark/JAR, ODBC 드라이버, DB 클라이언트, ML/프로파일링 패키지, 개발 도구. 이들은 인터넷 전용 기능은 아니며 실제 사용 범위에 따른 2차 경량화 대상이다. pandas/pyarrow/Jupyter 등은 핵심 실행·미리보기와 연결되므로 단순 삭제 대상에서 제외한다.

Dockerfile의 apt, CRAN, pip, GitHub 직접 설치와 베이스 이미지 pull은 **빌드 시** 외부 의존성이다. 실행 시 인터넷 차단과 별도 문제이므로, 빌드도 폐쇄망에서 수행하려면 사내 레지스트리·apt/npm/PyPI 미러 또는 사전 반입 아티팩트가 필요하다. 프런트엔드는 빌드 stage에서 생성하고 배포 이미지에는 필요한 정적 산출물만 포함하는 구성이 적합하다.

## 5. 유지할 기능과 삭제 시 깨지기 쉬운 경계

유지 권장 기능은 파이프라인/블록 모델, 로컬 Python/SQL 실행, 스케줄러/cron/백필/실행 이력, 내부 API 트리거, 웹 UI/코드 편집/로그/데이터 미리보기, 로컬 스토리지, 사용자/권한/로컬 시크릿, 사내 DB 연결이다. Redis, Kubernetes, Kafka, SMTP, LDAP/OIDC, 사내 Git, 내부 HTTP API는 필요에 따라 유지한다.

- `requests`, `aiohttp`, `httpx`는 공용 HTTP 라이브러리다. 사내 API도 사용하므로 인터넷 기능 제거를 이유로 전부 삭제하지 않는다.
- `mage_ai/ai/`에는 LLM 이외 유틸리티도 있다. `models/block/outputs.py`와 `server/utils/custom_output.py`는 `ai/utils/xgboost.py`를 참조하므로 먼저 이동하거나 연결을 정리해야 한다.
- `executor_factory.py`, streaming source/sink factory는 공급자별 lazy import를 사용한다. 연결 분기와 설정 검증을 지운 후 구현을 삭제한다.
- 삭제된 executor 설정이 기존 파이프라인에 남았을 때 로컬 실행으로 조용히 바뀌지 않도록 명시적 오류/마이그레이션을 추가해야 한다. 현재 factory의 fallback 동작에 주의한다.
- `repo_manager.py`, 프로젝트 모델, 기본 `metadata.yaml`, `io_config.yaml`, SQL 실행 분기, 프런트엔드 타입/선택지에도 클라우드 설정이 남아 있다.
- 파일을 제거하면서 기존 DB 마이그레이션 이력까지 삭제하지 않는다. 사내 계정/OAuth 토큰/스케줄 메타데이터와 클라우드 provider 구현은 별개다.
- `services/`, `cluster_manager/`, `authentication/`, `data_integrations/`를 이름만 보고 통째로 삭제하면 로컬 기능도 손상될 수 있다.
- `server/frontend_dist` 및 `frontend_dist_base_path_template`는 배포 산출물이다. TSX 소스 수정 후 정적 산출물을 재생성해야 기존 클라우드 메뉴가 배포본에 남지 않는다.

## 6. 권장 작업 순서와 완료 기준

1. **보존 범위 확정:** 기본안은 로컬 Python/SQL + 사내 DB + 스케줄링 + 로그/시크릿. MinIO/Ceph용 S3와 사내 OpenAI 호환 AI를 포함한다. Kubernetes, Kafka, Spark, dbt, Data Integration, 사내 SSO 필요 여부는 별도 선택으로 둔다.
2. **독립 빌드 확보:** 공개 `mage-ai[all]` 설치를 fork wheel 설치로 바꾸고 핵심/선택 의존성을 분리한다. 변경 전 기동·대표 파이프라인 결과를 기준으로 확보한다.
3. **자동 외부 통신 제거:** 통계 전송, 버전 조회, 벤더 동기화/중계, 시작 시 pip 설치, demo 추적을 정리한다.
4. **공급자별 수직 제거:** AWS/GCP/Azure 및 SaaS별로 UI → API/등록부 → 실행 분기 → 구현 → 의존성/템플릿을 한 묶음으로 정리한다.
5. **기존 설정 이관:** 원격 결과/로그/시크릿 이관 필요 여부를 판단하고, 제거된 connector/executor를 가진 파이프라인에는 수정할 설정을 명확히 알린다.
6. **오프라인 검증:** 서버와 작업 프로세스의 외부 egress 및 DNS 요청을 관찰하면서 기동, 로그인, 블록 실행, 예약 실행, 실패·재시도, 결과/로그 조회, 재시작을 확인한다. 브라우저도 별도로 외부 요청을 관찰한다.
7. **실제 경량화 측정:** 동일 플랫폼/빌드 조건에서 이미지 크기, 설치된 패키지/전이 의존성, 기동 시간, 유휴 메모리를 전후 비교한다. 현재 단계에서는 절감률을 추정하지 않는다.

애플리케이션의 내장 외부 연동을 지워도 사용자 Python 코드·터미널·임의 URL 요청 자체가 인터넷에 접근할 수는 있다. 외부 통신 금지가 요구사항이면 서버/워커의 egress를 내부 서비스 허용 범위로 제한해야 하며, 커넥터 삭제만으로 이를 보장했다고 볼 수 없다.

초기 구현 범위로는 **fork 독립 빌드 + 자동 외부 통신 제거 + S3 호환 저장 및 OpenAI 호환 AI 보완 + 그 외 클라우드 실행/저장/시크릿 제거 + SaaS 커넥터 및 의존성 정리**를 권장한다. Data Integration 전체, Spark/R, 벡터 DB/ML 기능 삭제는 실제 사내 사용 범위에 따라 후속 단계로 분리한다.

## 7. 추가 확정 사항: MinIO/Ceph 및 OpenAI 호환 AI

**S3 호환 기능은 유지한다.** `boto3`/`botocore`, `io/s3.py`, `services/aws/s3/`, S3 source/destination, 템플릿·등록부·UI를 보존한다. S3 로그·중간 결과 저장·streaming sink도 제거 목록에서 제외하되, 모든 경로가 사내 endpoint를 사용하도록 보완한다. AWS ECS/EMR/Secrets Manager/STS AssumeRole 등 퍼블릭 AWS 전용 경로와 분리한다.

| 경로 | 현재 endpoint 지원 | 후속 조치 |
|---|---|---|
| `mage_ai/io/s3.py` | `AWS_ENDPOINT`를 `endpoint_url`로 전달 | MinIO/Ceph 읽기·쓰기 검증 |
| Integration S3 source/destination | `aws_endpoint` 전달. 별도 AssumeRole 분기 존재 | 사내 자격증명 사용, 불필요한 AWS STS 경로 정리 |
| `s3_logger_manager.py` | 로그 설정의 `endpoint_url` 전달 | 저장·조회 검증 |
| `S3VariableManager` | `S3Storage(dirpath=...)`만 생성하며 endpoint를 명시적으로 전달하지 않음 | 사내 endpoint 설정 연결 |
| `services/aws/s3/s3.py` | client는 endpoint를 받지만 `resource()`는 인자 없이 `boto3.resource('s3')` 생성 | client/resource 설정 일치 |
| `streaming/sinks/amazon_s3.py` | 인자 없이 `boto3.client('s3')` 생성 | endpoint·자격증명 설정 전달 추가 |

SDK 환경변수만으로 모든 경로가 이미 호환된다고 가정하지 않는다. 사내 endpoint 누락 시 명확한 설정 오류를 반환하고, 주소 방식(path-style/virtual-host-style), 서명·리전, 사내 CA, multipart 업로드와 목록 조회를 실제 환경에서 검증한다.

**AI는 유지하되 현재 구현은 사내 OpenAI 호환 서버 연결을 위한 보완이 필요하다.**

- `orchestration/ai/config.py`의 `OpenAIConfig`에는 API key만 있고 `base_url`/`model` 필드가 없다.
- `ai/openai_client.py`는 SDK Chat Completions와 LangChain `OpenAI`/`LLMChain` 경로를 함께 사용한다. 두 경로에 공통 endpoint/model 설정을 명시적으로 전달하지 않는다.
- SDK Chat Completions 모델은 `gpt-4o`로 고정되어 있으며 `tools`와 강제 `tool_choice`를 사용한다.
- URL만 바꾸면 모든 기능이 작동한다고 판정할 수 없다. SDK/라이브러리 환경변수 처리도 실행 검증하지 않았다.

후속 구현 범위:

1. 사내 `base_url`, `model`, API key 설정을 추가하고 AI UI도 사내 모델 설정에 맞춘다.
2. 코드·주석·문서·블록·파이프라인 생성은 보존한다. 사내 endpoint가 없으면 미설정 상태로 표시하고 공개 endpoint로 fallback하지 않는다.
3. SDK Chat Completions 중심으로 호출 통합을 검토한다. LangChain 제거 시 프롬프트 생성·비동기 호출·응답 파싱도 함께 대체한다.
4. 서버/모델의 tool calling, 강제 tool 선택 및 기대 JSON 응답 지원을 확인한다. 미지원 시 명시적 기능 제한 또는 별도 JSON 프롬프트/파싱 경로가 필요하다.
5. 실제 사내 서버로만 요청되는지와 각 생성 기능 결과를 검증한다. 대상 제품/버전/모델은 아직 확인되지 않아 호환성은 미확정이다.

## 8. 기능 제거와 함께 수행할 UI 변경

UI 변경은 동일한 경량화 작업의 필수 범위다. 공급자 기능을 제거할 때 메뉴, 설정 폼, 선택지, 템플릿, 실행 버튼, API 호출, 안내 문구 및 배포 정적 산출물까지 함께 정리한다. 아래는 구현 계획이며 아직 UI 코드를 변경하지 않았다. 경로는 `mage_ai/frontend/` 기준이다.

| 사용자 화면 | 변경 내용 | 주요 연결 위치 |
|---|---|---|
| 탐색 메뉴·배포 안내 | 공개 Mage Deploy/Pro 진입 제거. 삭제된 화면으로 가는 링크 정리 | `components/Dashboard/VerticalNavigation.tsx`, `components/shared/Header/` |
| Compute 관리 | AWS EMR 카드·생성/리소스 폼 제거. 사내 Spark를 유지하면 Standalone cluster 화면 보존 | `pages/compute/`, `components/ComputeManagement/`, `interfaces/ComputeServiceType.ts` |
| 파이프라인·블록 실행 설정 | ECS/Cloud Run/ACI 및 EMR 종속 실행 선택지 제거. 로컬 실행, 필요시 K8s 유지 | `components/PipelineDetail/Settings/`, `components/BlockSettings/`, `interfaces/ExecutorType.ts` |
| 클러스터 선택·실행 상태 | 제거된 EMR 연결 버튼·상태 조회·Compute 링크 정리 | `components/PipelineDetail/ClusterSelection/`, `KernelStatus.tsx` |
| 데이터 연결·SQL 공급자 | 삭제한 클라우드/SaaS를 source/destination 목록과 설정 폼에서 제거 | `components/DataIntegrationModal/`, `components/IntegrationPipeline/`, `interfaces/DataSourceType.ts` |
| 블록·파이프라인 템플릿 | 제거된 커넥터·센서·외부 callback 템플릿을 검색/생성 목록에서 제외 | `components/PipelineDetail/AddNewBlocks/`, `components/CodeBlock/`, 백엔드 템플릿·카탈로그 |
| 트리거 | AWS 이벤트 조회·자격증명 안내 제거. 스케줄/내부 API 트리거 유지 | `components/Triggers/Edit/`, `Detail/` |
| 로그인·Git 연결 | 제거된 공개 OAuth 제공자 버튼·callback 경로 정리. 사내 인증과 Git 설정 보존 | `pages/sign-in.tsx`, `pages/oauth.tsx`, `components/Sessions/`, `pages/settings/workspace/sync-data.tsx` |
| 사용 통계·업데이트 | 통계 참여 설정, 공개 최신 버전 배너 및 관련 요청 제거 | `components/settings/workspace/Preferences.tsx`, `components/shared/Header/`, `context/Project/`, `interfaces/ProjectType.ts` |
| 워크스페이스 관리 | 클라우드 배포 옵션만 분리 제거. 사용자·권한·파일·실행 이력 화면은 보존 | `pages/manage/`, `pages/settings/` |

**유지할 S3 화면:** 표시 이름을 `S3 호환 스토리지 (MinIO/Ceph)`로 바꾸고 endpoint, bucket, access key/secret 참조, region, 필요시 주소 방식과 CA 설정을 제공한다. 실제 backend가 지원하는 필드만 연결하고, 연결 검증은 우선 비파괴 조회를 사용한다. 기존 설정 호환성을 위해 내부 식별자 `s3`/`amazon_s3`와 YAML 키는 표시 이름과 분리하여 유지한다. 로그/결과 저장도 같은 설정 원칙을 적용한다.

**유지할 AI 화면:** `components/AI/Setup.tsx`와 워크스페이스 설정에 사내 base URL, model, API key/secret 참조를 연결한다. OpenAI 가입·키 발급·Mage AI 홍보 안내는 정리한다. 현재 `AddNewBlocks/v2`, `CodeBlock/CommandButtons`, `CodeBlockV2/Editor` 등은 `project.openai_api_key`를 사용하므로, 생성 버튼 활성 조건도 서버가 알려주는 AI 설정 완료/지원 기능 상태로 변경한다. API 응답에 실제 키를 노출하여 활성 여부를 판단하지 않도록 한다. 미설정·연결 실패·모델의 기능 미지원 상태를 구분해서 표시한다.

**UI와 API의 일관성:** 보존할 provider/executor 목록을 하나의 정책으로 관리하고 UI 목록과 서버 검증에 함께 적용한다. 제거된 기능은 URL 직접 접근이나 수동 API 요청으로 실행되지 않아야 한다. 메뉴 숨김만으로 완료 처리하지 않는다. 기존 파이프라인에 삭제된 공급자 설정이 있으면 자동으로 다른 실행기로 바꾸지 않고 수정이 필요한 항목을 안내한다.

**완료 기준:** 삭제된 기능이 메뉴·검색·템플릿·설정에 나타나지 않고 관련 API를 호출하지 않아야 한다. S3 읽기/쓰기·로그/결과 조회와 AI 생성 기능을 UI에서 검증한다. 사내 SSO/권한/스케줄 실행도 회귀 확인한다. 프런트엔드 빌드 후 `server/frontend_dist` 및 base-path용 산출물을 갱신하고, 실제 배포 UI에서 외부 요청과 끊어진 링크를 확인한다.
