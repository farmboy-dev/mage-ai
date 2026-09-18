# R2 — SDK·이미지 경량화 상세 변경안 (R2a 적용 완료)

2026-09-18. R1은 `efe81e6db`로 로컬 커밋했다. GitHub push는 하지 않았다. 이 문서는 저장소 선언·잔여 코드·현재 개발 컨테이너의 설치 메타데이터를 읽어 작성했다. 이후 사용자 승인으로 R2a를 적용하고 별도 후보 이미지를 빌드했다. [검증 결과](DEPENDENCIES_R2_RESULT.ko.md)를 참고한다.

## 권장 적용 순서

R2a에서 아래 직접 의존성과 잔여 AWS 설정 경로를 정리하고 별도 태그로 이미지를 빌드한다. 결과를 검토한 다음 개발 환경 전환 및 R2b의 간접 의존성·기존 버전 충돌 해결 범위를 결정한다. 보존 기능을 없애서 패키지 수를 줄이지 않는다.

## R2a 수정 파일과 내용 — 승인 후 적용

| 파일 | 변경 내용 |
|---|---|
| `requirements.txt` | 아래 삭제 SDK의 직접 선언 및 cloud dbt adapter 4개 제거. 공용 라이브러리와 내부 기능 패키지 유지 |
| `setup.py` | azure/bigquery/google-cloud-storage/redshift/snowflake extras 제거. all·dbt extras의 해당 의존성도 동기화. s3·ai·spark·내부 DB extras 유지 |
| `mage_integrations/requirements.txt` | 삭제 integration의 SDK 직접 선언 제거. setup.py는 이 파일을 읽으므로 별도 중복 목록을 만들지 않음 |
| `mage_ai/settings/backends.py` | 남아 있던 AWSSecretsManagerBackend와 전용 BackendType 제거. 환경변수·기본값을 읽는 SettingsBackend 유지 |
| `mage_ai/settings/__init__.py` | AWS backend import와 생성 분기 제거. 기본 설정 호출 유지, 명시적인 미지원 backend는 일반 오류로 처리 |
| `mage_ai/tests/settings/test_backends.py` (신규) | 환경변수/기본값, 미지원 backend가 외부 클라이언트 생성 전에 실패하는지 검증 |
| `mage_ai/data_preparation/models/block/dbt/constants.py` | 삭제하는 Synapse 전용 adapter 이름 제거. SQLServer 및 그 의존성인 Fabric 처리는 보존 |
| `Dockerfile` | sparkmagic 설치·원격 예제 설정 다운로드·Livy kernelspec 설치 제거. 사용처 및 설치 의존성이 확인되지 않은 oscrypto의 Git 설치 제거. 나머지 내부 기능용 Git 설치 유지 |
| `dev.Dockerfile` | 현재 runtime 상속 방식 유지. R2 후보 runtime 태그를 build argument로 주입하여 검증; 구조 변경은 예정 없음 |
| `docs_refactor/LOCAL_BUILD.ko.md`, `DEV_SETUP.ko.md`, 신규 R2 결과 문서 및 README | 후보 이미지 빌드·검증 결과·전환과 복구 방법 기록 |

직접 선언 제거 대상:

- `aws-secretsmanager-caching`
- `google-api-core`, `google-api-python-client`, `google-cloud-bigquery`, `google-cloud-bigquery-storage`, `google-cloud-iam`, `google-cloud-pubsub`, `google-cloud-run`, `google-cloud-storage`, `google-ads`, `google-analytics-data`, `gspread`, `db-dtypes`
- `azure-eventhub`, `azure-identity`, `azure-keyvault-secrets`, `azure-keyvault-certificates`, `azure-mgmt-containerinstance`, `azure-storage-blob`
- `redshift-connector`, `snowflake-connector-python`, `facebook_business`, `simple_salesforce`, `stripe`, `twitter-ads`, `zenpy`, `teradatasql`
- `dbt-bigquery`, `dbt-redshift`, `dbt-snowflake`, `dbt-synapse`

각 파일에 실제 존재하는 선언만 제거한다.

## 조사에서 확인한 중요 경계

### 별도 AWS 설정 백엔드가 남아 있음

R1이 정리한 IO loader·DB 연결 경로와 별개로 `settings/backends.py`에 실제 `boto3.client('secretsmanager')` 생성 코드가 있고, `settings/__init__.py`의 factory로 선택할 수 있다. 삭제된 기능의 오류 호환 코드가 아닌 잔여 구현이다. SDK만 제거하면 동작이 불완전해지므로 위 두 파일을 함께 제거 범위에 포함한다. 기본 환경변수 설정과 Mage secrets, S3용 boto3/botocore는 유지한다.

### Azure SDK는 직접 선언을 지워도 다시 설치될 수 있음

현재 설치 메타데이터에서 `dbt-sqlserver 1.9.0 → dbt-fabric 1.9.3 → azure-identity` 의존성을 확인했다. 내부 SQL Server dbt를 유지하기 위해 R2a는 이 간접 의존성을 강제로 제거하지 않는다. Azure SDK 완전 제거는 adapter 교체·수정 여부를 별도 검토해야 한다. extras에만 있는 선택 의존성을 필수 의존성으로 잘못 계산하지 않도록 새 이미지 설치 목록으로 확인한다.

### Spark 및 공용 라이브러리 보존

Mage PySpark 커널은 IPython 기반이며 sparkmagic을 쓰지 않는 회귀 테스트가 있다. `SPARK_MASTER_HOST`, Spark UI, Python/PySpark 커널, `spark_config`, dbt-spark는 유지한다. 기본 개발 이미지의 실제 Java/PySpark 설치·클러스터 실행은 현재 보장되지 않으므로 새 이미지에서도 실서비스 연결 완료라고 표현하지 않는다.

`boto3/botocore`, `openai`, `requests/httpx`, Singer, pyarrow, deltalake, 내부 DB 드라이버, dbt-core 및 내부 adapter는 보존한다. `lxml`은 XML/HTML 등 공용 용도를 고려해 이번에 제거하지 않는다. Google 인증 등 공용·간접 의존 패키지도 이름만 보고 삭제하지 않는다.

### 현재 이미지의 기존 의존성 충돌

R2 변경 전에 실행한 `python -m pip check` 결과는 다음 5건이다.

| 소비 패키지 | 요구 조건 | 현재 설치 |
|---|---|---|
| typing-inspection 0.4.4 | typing-extensions >=4.15.0 | 4.11.0 |
| singer-python 5.13.0 | backoff ==1.8.0 | 2.2.1 |
| singer-python 5.13.0 | jsonschema ==4.17.0 | 4.26.0 |
| singer-python 5.13.0 | simplejson ==3.11.1 | 4.1.2 |
| dbt-mysql 1.7.0a1 | dbt-core ~=1.8.0 | 1.10.20 |

R2a에서는 새 충돌을 추가하지 않는지 기준과 비교한다. 위 충돌이 남으면 이미지가 완전히 정합하다고 보고하지 않고, R2b에서 버전·fork metadata·adapter 변경안을 별도 제시한다. 현재 실행 컨테이너에서 수동 uninstall하거나 무리하게 downgrade하지 않는다.

## 빌드 및 검증

1. 기존 실행 이미지 ID·패키지 목록·크기·pip check를 기준 자료로 저장한다.
2. wheel metadata에서 제거한 extras와 직접 SDK 요구가 사라졌는지 검사한다.
3. `Dockerfile`로 별도 `localhost/mage-fork:r2-candidate` 태그를 빌드한다. 현재 호스트의 `POLARS_PACKAGE=polars-lts-cpu` 설정을 유지한다.
4. dev backend도 후보 runtime으로 별도 태그를 빌드한다. 기존 3000/6789 및 원본 3100 컨테이너는 검증 중 그대로 유지한다.
5. 설치 패키지·이미지 크기·간접 재설치 사유·pip check를 비교한다. 공통 base layer가 있으므로 선언 개수로 절감 용량을 추정하지 않는다.
6. 격리 프로젝트로 core import, S3/OpenAI 호환 회귀, 내부 connector 로딩, 로컬 파이프라인, Spark kernel/env, dbt adapter 로딩, API·UI 및 외부 연결 감사를 수행한다.
7. 결과를 문서로 보고한다. 후보 이미지 검증 후 개발 환경 전환은 결과 검토 단계에서 결정한다.

## 이번 적용에서 제외

- Couchbase libssl.so.1.1·Delta Lake PyDeltaTableError 기존 문제 수정(R3).
- Datadog/Hugging Face/Google Chat/Azure DevOps 등 실제 잔여 기능의 일괄 제거. 각각 사용처와 UI를 포함한 별도 계획 필요.
- `dev.spark.Dockerfile` 및 `integrations/*/Dockerfile` 등 별도 이미지의 일괄 개편. legacy Spark 이미지에도 sparkmagic·dbt-synapse 설치가 남아 있으므로 전체 빌드 경로 정리가 끝났다고 보고하지 않는다.
- 빌드 시 인터넷 다운로드 완전 제거와 패키지 mirror 구성.

**R2a의 위 파일·SDK·AWS 설정 backend 정리와 격리 후보 이미지 빌드/검증을 승인 후 완료했다.** R2b 버전 충돌 수정, 실제 개발 컨테이너 교체, R3는 결과와 상세 변경안을 검토한 뒤 진행한다.
