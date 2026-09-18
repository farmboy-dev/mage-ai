# C2b GCS 저장·로그 및 클라우드 Secrets 제거안 — 승인 대기

2026-09-18. 다음 단계 적용을 위한 검토 문서다. 이 단계의 애플리케이션 코드는 아직 변경하지 않았다. C2a 변경은 작업 트리에 있으며 마지막 커밋은 `b49f9c837`이다.

## 목적과 적용 순서

기본 커넥터를 제거해도 남아 있는 GCS 결과·로그 저장, Azure Key Vault, AWS Secrets Manager 로더를 제거한다. 사용자 승인 후 C2a 완료분을 먼저 별도 로컬 커밋하고, C2b를 구현·검증한다. GitHub push는 하지 않는다. 코드·주석·오류 메시지는 영어로 작성한다.

## 파일별 적용 범위

경로는 별도 표기가 없으면 `mage_ai/` 기준이다.

| 파일 | 변경 내용 |
|---|---|
| `data_preparation/storage/gcs_storage.py` | GCS 저장 구현 삭제 |
| `data_preparation/variable_manager.py` | `GCSVariableManager` 삭제. factory와 직접 생성 경로에서 최종 variables_dir의 `gs://` 설정을 파일 작업·SDK 초기화 전에 거절. 로컬 및 S3 경로 유지 |
| `data_preparation/logging/gcs_logger_manager.py` | GCS 로그 구현 삭제 |
| `data_preparation/logging/logger_manager_factory.py` | GCS 생성 분기를 영어 오류로 교체. `type: gcs`를 로컬 로그로 묵시 전환하지 않음 |
| `data_preparation/logging/__init__.py` | GCS 활성 타입 제거. 기존 문자열 설정은 factory의 명시적 차단으로 처리. file/s3 및 로그 레벨·보존기간 유지 |
| `services/azure/key_vault/key_vault.py`, `__init__.py` | 전용 모듈 2개 삭제. import 시 `DefaultAzureCredential` 및 SecretClient 초기화 경로 제거 |
| `data_preparation/shared/utils.py` | Azure SDK import 제거. `azure_secret_var` 이름은 영어 이전 안내 오류만 내는 호환 함수로 유지하여 기존 템플릿에 명확한 실패 원인 제공. `env_var`, `mage_secret_var`, `json_value` 유지 |
| `orchestration/db/setup.py` | `AZURE_SECRET_DB_CONN_URL` 사용 시 명시적 오류. 직접 DB URL 또는 POSTGRES 환경변수 안내. 실패 후 다른 DB로 조용히 넘어가는 동작 제거 |
| `io/config.py` | `AWSSecretLoader`의 Secrets Manager 구현 제거. 공개 이름은 생성 시 영어 이전 안내 오류만 내는 호환 클래스로 유지. `ConfigFileLoader` 및 S3용 설정 유지 |
| `shared/constants.py`, `orchestration/constants.py` | 기존 GCS URI·Azure 환경변수 식별 상수는 차단에 필요한 범위에서 유지. 지원 기능으로 해석하지 않음 |
| `tests/data_preparation/storage/test_gcs_storage.py` | 삭제 구현 전용 테스트 제거, 새 정책 테스트로 대체 |
| `tests/streaming/sinks/test_google_cloud_storage.py` | C1에서 이미 삭제한 sink를 import하는 잔여 테스트 정리. 이번 조사에서 발견한 C1 누락 보완 |
| 새 `tests/data_preparation/test_cloud_runtime_removed.py` | GCS 저장·로그, Azure 변수·DB 설정, AWS 로더의 연결 전 차단과 로컬/S3/내부 Secrets 보존 검증 |
| `docs_refactor/` | 이전 방법·검증 결과 및 인덱스 갱신 |

실제 코드 변경 시 위 경로 외 추가 수정이 필요하면 변경 이유와 범위를 먼저 보고한다. SDK 전용 구현 파일은 4개, 삭제 구현에 종속된 테스트 파일은 2개다.

## UI 및 기존 프로젝트 영향

- 이번 대상의 프런트엔드 컴포넌트·타입 검색에서 활성 전용 선택 메뉴는 찾지 못했다. 따라서 예정된 JSX·레이아웃 변경은 없다. Browser/System/mocks.ts의 예시 경로는 그대로 둔다.
- 결과·로그·Secrets 화면과 Python/PySpark 커널 선택은 유지한다. 로컬/S3 로그 조회 및 일반 실행 화면을 회귀 확인한다.
- `gs://` 중간 결과, `logging_config.type: gcs`, `azure_secret_var`, `AZURE_SECRET_DB_CONN_URL`, `AWSSecretLoader`를 사용하는 기존 설정·코드는 실행 또는 해당 설정 초기화 시 오류가 발생한다. 설정에 따라 서버 기동 단계에서 실패할 수도 있다.
- 기존 원격 결과·로그를 자동 이관하거나 삭제하지 않는다. 사용자가 별도로 이관한 후 로컬/S3 경로로 설정을 변경해야 한다. 프로젝트의 실제 설정·자격증명을 임의로 덮어쓰지 않는다.
- `azure_secret_var`는 `env_var` 또는 내부 `mage_secret_var`로, AWS 로더는 내부 설정 파일·환경변수·내부 Secrets 방식으로 이전한다. 오류에는 실제 비밀값을 포함하지 않는다.

## 보존 및 제외 범위

S3/MinIO/Ceph와 boto3/botocore, OpenAI 호환 AI, PySpark, 로컬 저장·로그, 내부 DB 및 Mage Secrets를 유지한다. 원본 3100 비교 환경과 Compute 라우팅은 변경하지 않는다.

PubSub/Kinesis/SQS/Event Hub 등의 스트리밍, 나머지 SaaS integrations, dbt 어댑터, 전체 SDK·이미지 경량화는 후속 단계다. 이번에는 requirements/setup SDK 선언 제거·수동 uninstall·이미지 재빌드를 하지 않는다. 따라서 Google/Azure 전체 제거 완료나 이미지 용량 감소로 보고하지 않는다.

## 검증 및 완료 조건

1. 기존 58개 회귀 검증과 신규 정책 테스트 수행. 삭제된 모듈을 import하는 테스트·실행 경로 잔존 검색.
2. GCS 경로가 로컬 디렉터리로 생성되지 않으며, GCS 로그가 file logger로 fallback하지 않는지 확인.
3. Azure/AWS 차단 경로에서 SDK/client 호출이 발생하지 않는지 mock으로 검증. 환경변수·내부 Secrets·직접 DB 접속 설정 유지 확인.
4. 격리 프로젝트에서 정상 로컬 파이프라인 실행·결과 및 로그 조회, S3 호환 회귀, 실패 설정의 오류 노출 검증. 실제 사내 endpoint는 요구하지 않는다.
5. Python 구문 검사, TypeScript 검사, UI smoke 및 격리 백엔드 외부 연결 감사 수행.
6. 결과 문서 작성, 임시 컨테이너 정리. 개발 서버 반영이 필요하면 정상 설정에서 재시작 후 응답 확인.

## 검토 요청

위 C2b 범위 및 C2a 선행 로컬 커밋을 승인받은 뒤 적용한다. 승인 전에는 문서 준비 외 코드 변경·커밋·재시작을 진행하지 않는다.
