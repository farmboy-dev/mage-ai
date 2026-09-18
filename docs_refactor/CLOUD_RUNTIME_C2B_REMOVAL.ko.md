# C2b GCS 저장·로그 및 클라우드 Secrets 제거 결과

2026-09-18. [승인된 변경안](CLOUD_RUNTIME_C2B_PLAN.ko.md)에 따라 적용했다. C2a 완료분과 C2b 검토 문서를 먼저 로컬 커밋 `6a28ea7db`에 저장했다. 이번 C2b 구현은 아직 추가 커밋하지 않았으며 GitHub push는 하지 않았다.

## 적용 내용

- GCSStorage, GCSLoggerManager 및 Azure Key Vault 전용 모듈 2개 삭제.
- GCSVariableManager 제거. VariableManager factory 및 직접 생성 시 명시적·기본 설정의 최종 `gs://` 경로를 LocalStorage 초기화 전에 거절.
- LoggerType의 GCS 선택 제거. logger factory가 전달된 설정 또는 기본 프로젝트 설정의 `type: gcs`를 거절. file logger로 자동 전환하지 않음.
- Azure SDK import 및 import 시 인증 클라이언트 생성 제거. `azure_secret_var`는 영어 이전 안내 오류만 반환하는 호환 함수로 유지.
- `AZURE_SECRET_DB_CONN_URL` 경로는 명시적 오류로 전환. 실제 사용되는 직접 Postgres 환경변수는 `DB_USER`, `DB_PASS`, `DB_NAME`, `DB_HOST`, `DB_PORT`이며 `MAGE_DATABASE_CONNECTION_URL`도 기존 방식으로 사용 가능.
- AWSSecretLoader는 생성 시 영어 이전 안내 오류만 내는 호환 클래스로 교체. boto3 Secrets Manager 호출 제거.
- 삭제된 GCS storage 전용 테스트와 C1에서 남았던 GCS streaming sink 테스트 제거. 신규 런타임 정책 테스트 추가.
- 프런트엔드 코드·레이아웃 변경 없음. 내부 Secrets·S3·AI·PySpark 기능 유지.

## 기존 설정 이전

| 기존 설정/코드 | 필요한 변경 |
|---|---|
| `variables_dir: gs://...` | 결과 데이터를 별도 이관한 뒤 로컬 또는 S3 호환 경로로 변경 |
| `logging_config.type: gcs` | 기존 로그를 별도 이관하고 `file` 또는 `s3` 로깅 설정 |
| `azure_secret_var(...)` | 환경변수 `env_var(...)` 또는 내부 `mage_secret_var(...)` 사용 |
| `AZURE_SECRET_DB_CONN_URL` | 환경변수를 제거하고 직접 DB URL 또는 위 `DB_*` 환경변수 사용 |
| `AWSSecretLoader(...)` | ConfigFileLoader, EnvironmentVariableLoader 또는 내부 Mage Secrets로 이전 |

원격 데이터·로그 및 사용자 설정을 자동 이관·삭제하지 않았다. 기존 클라우드 설정은 초기화·실행 시 실패하며 사용 경로에 따라 서버 기동에도 영향을 줄 수 있다. SDK 모듈을 직접 import하던 사용자 코드는 ImportError가 발생할 수 있다. 오류 메시지에 실제 비밀값은 포함하지 않는다.

## 검증

- Python 68개 통과: 기존 58개, 신규 런타임 정책 7개, 기존 로그 보존기간 3개. S3/AI 호환·Spark 설정 회귀 포함.
- 신규 정책 검증: 명시적/기본 GCS 경로 차단, 로컬/S3 factory 보존, GCS 로그 fallback 방지, Azure/AWS SDK import 미발생, 비밀값 미노출, 내부 Secrets·환경변수·Postgres 설정 보존.
- 전체 TypeScript 검사 및 변경 Python 구문 검사, `git diff --check` 통과.
- 격리 프로젝트에서 실제 loader → transformer → exporter 실행. 결과 `[2, 4, 6]` 확인.
- 로컬 로그 실제 쓰기·읽기 통과. 파이프라인 조회·로그 API 오류 없음. 로그 API 응답 검증과 별도로 LoggerManager의 실제 로그 내용을 확인했다.
- 실제 Jinja 템플릿의 Azure 변수 및 GCS URI 오류 확인.
- 기존·신형 블록 메뉴 및 Browse templates 진입 확인, JavaScript 오류 0개. S3·내부 DB 선택 유지.
- 격리 백엔드 외부 연결 감사 기록 없음.
- 개발 서버 재시작 후 API 응답 확인. 3000 개발 UI에서 사용 가능. 원본 3100 환경은 변경하지 않음.

초기 테스트에서 AWS 호환 클래스에 남은 추상 베이스 클래스 때문에 의도한 오류가 나오지 않는 문제를 찾아 상속을 제거했다. Postgres 테스트의 환경변수명도 실제 DB_* 상수에 맞게 수정했다. 최종 68개 결과는 수정 후 전체 재실행 결과다.

검증 로그: `/tmp/mage-c2b-tests.log`, `/tmp/mage-c2b-tsc.log`, `/tmp/mage-c2b-pipeline.log`, `/tmp/mage-c2b-browser.log`. UI 검증에는 기존 C2a 브라우저 스크립트를 재사용했다.

## 한계 및 후속 작업

- 실제 사내 MinIO/Ceph·AI endpoint 연결과 Spark 연산을 새로 검증한 것은 아니다.
- SDK 의존성 선언·설치 패키지와 이미지 크기는 변경하지 않았다. 전체 SDK 정리 및 이미지 재빌드는 C3 범위다.
- 클라우드 streaming·나머지 SaaS integration은 남아 있다. 다음 단계도 파일별 변경안을 제출하고 승인 후 진행한다.
