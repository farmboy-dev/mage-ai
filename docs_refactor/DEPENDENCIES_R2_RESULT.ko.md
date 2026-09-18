# R2a — SDK·이미지 경량화 결과

2026-09-18. [승인된 R2a 변경안](DEPENDENCIES_R2_PLAN.ko.md)을 적용했다. R1 기준 커밋은 `efe81e6db`이며, R2a는 아직 커밋·push하지 않았다. 기존 개발 컨테이너의 이미지는 교체하지 않았다.

## 적용 내용

- `requirements.txt`, `setup.py`, `mage_integrations/requirements.txt`에서 삭제 기능의 직접 SDK 선언 및 cloud dbt adapter 4개를 제거했다. azure/bigquery/google-cloud-storage/redshift/snowflake extras도 제거했다.
- `settings/backends.py`의 AWSSecretsManagerBackend와 전용 enum, `settings/__init__.py`의 생성 분기를 제거했다. 환경변수·기본값 설정은 유지하고, 미지원 backend/인자는 일반 오류로 처리한다. 오류 발생 시 기존 backend를 바꾸거나 boto3 클라이언트를 생성하지 않는다.
- dbt의 Synapse 전용 상수를 제거했다. 내부 SQL Server용 Fabric 처리는 유지했다.
- `Dockerfile`의 sparkmagic 설치·Livy kernelspec 등록·원격 예제 설정 다운로드 및 oscrypto Git 설치를 제거했다. `dev.Dockerfile`의 기존 runtime 상속 구조는 수정 없이 유지했다.
- S3/MinIO/Ceph용 boto3/botocore, OpenAI 호환 API, Python/PySpark kernel·UI, `SPARK_MASTER_HOST`, 내부 DB·dbt adapter는 유지했다.

## 후보 이미지 및 실제 감소량

| 구분 | 기존 | R2a 후보 | 감소 |
|---|---:|---:|---:|
| runtime 이미지 | 4,113,529,712 bytes | 3,237,899,058 bytes | 875,630,654 bytes, 약 21.3% |
| dev backend 이미지 | 4,281,678,273 bytes | 3,403,199,372 bytes | 878,478,901 bytes, 약 20.5% |
| 설치 Python distribution 수 | 426 | 341 | 85개 |

Podman image inspect의 Size 기준이며, registry 압축 전송량 또는 공유 layer를 고려한 호스트 디스크 절감량과는 다르다. 기존 이미지를 보존했으므로 현재 호스트 디스크 사용량이 위 수치만큼 줄었다는 의미가 아니다.

- 기존 runtime: `39c86b0a607e`, `localhost/mage-fork:dev-base`
- 후보 runtime: `daab8b51e344`, `localhost/mage-fork:r2-candidate`
- 기존 dev backend: `e62b35d4d551`, `localhost/mage-fork-dev:backend`
- 후보 dev backend: `4c4f4da607c7`, `localhost/mage-fork-dev:r2-candidate`

전체 패키지 차이는 [JSON 기록](DEPENDENCIES_R2_PACKAGES.json)에 있다. 새로 추가된 distribution은 없고, 제거된 전용 SDK의 간접 의존성도 함께 줄었다. wheel metadata에서 해당 직접 의존성 및 extras 제거를 확인했다.

## 남아 있는 간접 의존성 및 버전 차이

삭제 선언 대상 중 실제 후보 이미지에 남은 것은 `azure-identity 1.25.3`이다. 보존한 `dbt-sqlserver → dbt-fabric → azure-identity` 경로 때문이다. 강제로 uninstall하지 않았다. Google 인증 등 공유 의존성까지 모두 제거한 상태는 아니다.

재빌드 시 resolver에 따라 기존보다 버전이 바뀐 패키지는 azure-identity, msal, certifi, idna, platformdirs, wcwidth 6개다. 직접 pin이 제거된 Azure 인증 라이브러리 및 범위 지정된 간접 의존성의 해석 결과이며, 모든 의존성이 고정된 lockfile 빌드는 아니다. 보존한 dremio-flight/Singer/dbt-mysql/sqlglot Git 소스 커밋은 기존 설치와 같았다.

`pip check`는 기존과 동일한 5건을 보고한다. 추가 충돌은 발견되지 않았다. typing-inspection/typing-extensions 1건, Singer의 backoff/jsonschema/simplejson 3건, dbt-mysql/dbt-core 1건이다. 상세 버전은 [R2 변경안](DEPENDENCIES_R2_PLAN.ko.md)에 기록했다. 패키지 정합성 검사가 통과했다고 보고하지 않으며, R2b에서 별도 변경안으로 해결한다.

## 검증

| 검사 | 결과 |
|---|---|
| runtime 및 dev backend 빌드 | 별도 태그로 성공, POLARS_PACKAGE=polars-lts-cpu 유지 |
| wheel metadata 및 설치 패키지 | 삭제 직접 SDK 요구 제거; azure-identity 외 대상 패키지 미설치; sparkmagic/oscrypto 미설치 |
| Python 회귀 테스트 | 후보 runtime에서 118개 통과 |
| 테스트 fixture | wheel에 테스트용 JSON이 없어 최초 9건 실패. 해당 samples 디렉터리만 읽기 전용 mount한 뒤 전체 통과. 애플리케이션 코드는 설치 wheel 사용 |
| 핵심 import | Mage 서버·S3·OpenAI·boto3 성공 |
| 내부 dbt adapter import | PostgreSQL/MySQL/SQL Server/Spark/DuckDB/ClickHouse/Trino 성공 |
| 설치 wheel smoke | 별도 소스 mount 없이 API·bundled frontend HTTP 응답 및 로컬 3블록 파이프라인 통과, JSON 값 2/4/6 확인 |
| API | 삭제/미등록 API 60개 요청 모두 404; 미등록 설정 거절; 기본/S3/integration template 생성 성공 |
| 브라우저 | 기존 3000 frontend를 격리 후보 dev backend 6788로 연결해 검사. Sources 12개/Destinations 13개, 브라우저 오류 0개 |
| 외부 연결 감사 | smoke 및 격리 API/UI 검사 경로에서 차단/기록된 시도 0건 |
| 개발 환경 | 기존 3000/6789 HTTP 200 유지, 후보 이미지로 교체하지 않음 |
| 변경 형식 | git diff --check 통과 |

TypeScript 코드는 이번에 수정하지 않았다. Spark 검증은 kernel 설정·초기화 경로·환경변수 우선순위 회귀 테스트이며, 실제 Spark 클러스터 연결 검증은 아니다. S3/AI도 로컬 대체 서비스와 mock 기반 검증이며 사내 endpoint 연결은 미확인이다. dbt adapter import 성공이 각 DB에서 dbt 실행까지 확인했다는 의미는 아니다.

## 잔여 문제와 다음 검토

Couchbase의 libssl.so.1.1 누락과 Delta Lake writer의 PyDeltaTableError import 실패는 후보 이미지에서도 재현했다. 이 두 보존 기능은 R3에서 수정한다. 기존 의존성 충돌 5건은 R2b 대상이다.

Datadog/Hugging Face/Google Chat/Azure DevOps 등 실제 잔여 기능, 별도 legacy Spark 이미지의 설치 경로, 빌드 네트워크 의존성은 이번 범위 밖이다. 모든 클라우드 코드·의존성이 제거됐다는 의미는 아니다.

현재 3000/6789 개발 환경은 기존 의존성 이미지를 유지한다. 저장소 소스를 mount하므로 이번 Python 코드 변경은 해당 환경에도 보이지만, 패키지 경량화 효과는 후보 이미지에만 있다. 3100 원본 비교 환경과 프로젝트 볼륨은 변경하지 않았다. 후보 이미지 전환은 이 결과 검토 후 진행하며, 이전 이미지 태그는 복구용으로 보존한다.

실행 로그·검사 스크립트는 호스트 `/tmp/mage-r2/`에 있으며 임시 자료다. 핵심 결과 및 패키지 차이는 이 문서 폴더에 보존했다.
