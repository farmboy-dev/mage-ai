# R1 — 잔여 호환 코드 정리 결과

2026-09-18. 사용자 승인 범위인 R1을 적용했다. 기준 커밋은 `d0d25e265`이며 R1 변경은 이후 `efe81e6db`로 로컬 커밋했다. GitHub에는 올리지 않았다. [변경안](FINAL_CLEANUP_PLAN.ko.md)과 [역사적 제거 목록](REMOVED_FEATURES_INVENTORY.ko.md)은 함께 보존한다.

## 적용 내용

- `shared/cloud_features.py`의 제거 이름 목록과 공급자별 거절 코드를 삭제했다. `shared/supported_features.py`에서 현재 지원하는 connector, executor, template, storage를 검증한다. integration 및 streaming은 source/destination 방향을 구분하고 동적 import·초기화 전에 검사한다.
- 오류만 반환하던 Cluster/ComputeCluster/ComputeConnection/ComputeService의 resource·policy·presenter 및 공통 RemovedCloudResource, 총 13개 파일을 삭제했다. 프런트엔드 API 등록도 제거했다. 미등록 resource·parent·child는 일반 HTTP 404를 반환한다. 정상 리소스 내부의 ImportError는 404로 숨기지 않는다.
- EMR 전용 CLI, 미사용 executor enum, 클라우드 Secrets 호환 함수·클래스·DB 환경변수 처리, 삭제한 공급자 전용 IO 설정 키를 제거했다. 로컬/S3 저장과 file/S3 로그는 유지하며 잘못된 저장 scheme은 디렉터리 생성·설정 저장 전에 거절한다.
- 프로젝트 저장은 지원 설정을 기준으로 검사한다. 기존 프로젝트 파일을 자동 정리하지 않으며 기존 확장 필드는 보존한다.
- BigQuery/Snowflake 전용 블록 설정 입력과 BigQuery partition 옵션, 이미 삭제한 모듈의 브라우저 mock 경로 108개를 정리했다. Delta Lake S3 partition 옵션은 유지한다.
- 기존 제거 목록 중심 테스트를 지원 기능·미등록 값 중심으로 전환했다. 추가 의존 파일인 GCS URL helper, UI 두 파일, streaming factory 테스트, IO 설정 로더 테스트도 보고 후 정리했다.

## Spark 및 내부 기능 보존

`PipelineType.PYSPARK`, Python/PySpark 커널 선택, 기존 Spark UI, `spark_config`, `SPARK_MASTER_HOST`는 유지한다. `executor_type: pyspark`였던 EMR 전용 실행 경로와는 별개다.

SparkSession 생성 시 명시적인 `spark_config.spark_master`가 우선하고, 없으면 `SPARK_MASTER_HOST`, 그마저 없으면 `local`을 사용한다. 설정 유무 및 우선순위를 mock 기반 회귀 테스트로 확인했다. 이번 검증은 실제 Spark 클러스터 연결 검증이 아니다.

S3/MinIO/Ceph, OpenAI 호환 API, K8S, 내부 DB, Mage secrets와 환경변수 템플릿은 보존했다. `/compute` 페이지와 kernel UI는 이번 삭제 대상이 아니다.

## 검증 결과

| 검증 | 결과 |
|---|---|
| API·connector·executor·streaming·template·S3·AI·Spark·로그 관련 Python 테스트 | 95개 통과 |
| IO 설정 로더·프로젝트 설정·저장 경로 기존 테스트 | 21개 통과; 삭제 키를 쓰던 6개 테스트는 S3/PostgreSQL 등 보존 키로 전환 |
| TypeScript | `yarn tsc --noEmit` 통과 |
| 변경 형식 | `git diff --check` 통과 |
| 격리 서버의 삭제 API 및 임의 미등록 API | 60개 실제 HTTP 요청: collection/member/nested × GET/POST/PUT/DELETE 모두 404 |
| 잘못된 connector/provider/template 및 integration 방향 | 공통 API 오류 코드 400, 거절된 블록 미저장 |
| 정상 블록 생성 | 기본 loader, S3 loader, S3 integration template 성공 |
| 인증 | 실제 개발 backend의 미인증 pipelines 요청 401; 인증 회귀 테스트 통과 |
| 브라우저 | Sources 12개·Destinations 13개 표시, 검사 중 브라우저 오류 0개 |
| 로컬 파이프라인 | 격리 프로젝트 3개 블록 실행 성공; JSON 결과의 value 2/4/6 확인 |
| 외부 연결 감사 | 격리 실행의 outbound 감사 기록 0건 |

테스트 프로젝트·DB는 `/tmp`에 격리했다. 실제 사내 서비스 endpoint·인증정보가 제공되지 않아 MinIO/Ceph·AI·Spark 실서비스 연결은 확인하지 않았다. 감사 결과는 위 실행 경로에 한정하며 모든 기능의 외부 통신이 제거됐다는 의미가 아니다.

## 설정 이관 및 남은 범위

과거 `AWS_DB_SECRETS_NAME`·`AZURE_SECRET_DB_CONN_URL`은 이제 읽지 않는다. 전용 오류 없이 기본 DB 설정으로 진행할 수 있으므로 해당 환경을 사용하던 배포는 직접 DB URL 또는 DB_* 설정으로 이관해야 한다. `AWSSecretLoader` import와 `azure_secret_var` 템플릿 함수도 더 이상 제공하지 않는다.

SDK·requirements·Docker 이미지 경량화는 R2 승인 범위로 남겼다. Datadog metrics, Hugging Face AI, Google Chat 및 실제 사용하는 K8S 클라우드 annotation 등도 이번 오류 전용 호환 코드 정리와 구분해 후속 변경안을 작성해야 한다.

Couchbase의 `libssl.so.1.1` 누락과 Delta Lake writer의 `PyDeltaTableError` import 실패는 이전 커밋에서도 확인한 기존 이미지 호환성 문제다. 이번 작업으로 해결하지 않았으며 R3에서 보존 기능으로 수정한다. UI에 표시된 모든 커넥터가 현재 이미지에서 실행된다는 의미는 아니다.
