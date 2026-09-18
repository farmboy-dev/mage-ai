# C2c 클라우드 스트리밍 제거 변경안 — 승인 후 적용

2026-09-18. C2b를 로컬 커밋 `04836802d`에 저장한 뒤 조사했다. 사용자 승인 후 적용했다. [검증 결과](CLOUD_STREAMING_C2C_REMOVAL.ko.md)를 참고한다. 아래는 승인 당시의 변경안이다. GitHub push는 하지 않았다.

## 제거 범위

| 서비스 | Source | Sink |
|---|---|---|
| Amazon SQS | 제거 | 기존 구현 없음 |
| Amazon Kinesis | 제거 | 제거 |
| Google Cloud Pub/Sub | 제거 | 제거 |
| Azure Event Hub | 제거 | 기존 구현 없음 |
| Azure Data Lake | 기존 구현 없음 | 제거 |

SQS·Kinesis는 현재 구현에서 boto3의 해당 AWS 클라이언트를 생성한다. S3 호환 경로와 별개의 기능이므로 이 범위에서는 제거 대상으로 제안한다.

## 삭제할 전용 파일 21개

구현 7개, YAML 템플릿 7개, 해당 구현 전용 테스트 7개다.

- `mage_ai/streaming/sources/amazon_sqs.py`
- `mage_ai/data_preparation/templates/data_loaders/streaming/amazon_sqs.yaml`
- `mage_ai/tests/streaming/sources/test_amazon_sqs.py`
- `mage_ai/streaming/sources/kinesis.py`
- `mage_ai/data_preparation/templates/data_loaders/streaming/kinesis.yaml`
- `mage_ai/tests/streaming/sources/test_kinesis.py`
- `mage_ai/streaming/sources/google_cloud_pubsub.py`
- `mage_ai/data_preparation/templates/data_loaders/streaming/google_cloud_pubsub.yaml`
- `mage_ai/tests/streaming/sources/test_google_cloud_pubsub.py`
- `mage_ai/streaming/sources/azure_event_hub.py`
- `mage_ai/data_preparation/templates/data_loaders/streaming/azure_event_hub.yaml`
- `mage_ai/tests/streaming/sources/test_azure_event_hub.py`
- `mage_ai/streaming/sinks/kinesis.py`
- `mage_ai/data_preparation/templates/data_exporters/streaming/kinesis.yaml`
- `mage_ai/tests/streaming/sinks/test_kinesis.py`
- `mage_ai/streaming/sinks/google_cloud_pubsub.py`
- `mage_ai/data_preparation/templates/data_exporters/streaming/google_cloud_pubsub.yaml`
- `mage_ai/tests/streaming/sinks/test_google_cloud_pubsub.py`
- `mage_ai/streaming/sinks/azure_data_lake.py`
- `mage_ai/data_preparation/templates/data_exporters/streaming/azure_data_lake.yaml`
- `mage_ai/tests/streaming/sinks/test_azure_data_lake.py`

## 공통 코드 변경

| 파일 | 변경 |
|---|---|
| `mage_ai/streaming/sources/source_factory.py` | 공급자 4개 분기·import 제거, 제거 정책을 import/client 생성 전에 검사 |
| `mage_ai/streaming/sinks/sink_factory.py` | 공급자 3개 분기·import 제거, 기존 제거 정책 유지 |
| `mage_ai/shared/cloud_features.py` | `amazon_sqs`, `kinesis`, `google_cloud_pubsub`, `azure_event_hub`, `azure_data_lake`를 제거 집합에 추가. 기존 API·템플릿 경로 검증과 연결 |
| `mage_ai/streaming/constants.py` | 기존 enum은 메타데이터 식별용으로 유지. 실행 지원은 factory·정책에서 제거 |
| `mage_ai/frontend/components/PipelineDetail/AddNewBlocks/utils.tsx` | streaming loader/exporter 선택 목록에서 해당 공급자 제거 |
| `mage_ai/frontend/interfaces/DataSourceType.ts` | 활성 표시 이름 매핑에서 제거. 기존 enum 식별자는 유지 |
| `mage_ai/data_preparation/executors/streaming_pipeline_executor.py` | YAML source와 모든 YAML sink를 변수 치환 후 먼저 검증. 제거된 sink 때문에 실패할 작업에서 source client가 먼저 시작되지 않도록 초기화 순서 조정. 치환한 설정 재사용 |
| `mage_ai/tests/streaming/sources/test_source_factory.py` | 삭제 구현 import 및 성공 기대 테스트 제거. 내부 브로커 factory 검증 보존 |
| `mage_ai/tests/streaming/sinks/test_sink_factory.py` | 제거된 sink의 연결 전 오류 및 보존 sink 경로 검증 확장 |
| `mage_ai/tests/data_preparation/test_cloud_connectors_removed.py` | 확장된 제거 목록의 API·템플릿·직접 실행 거절 검증 |
| 신규 `mage_ai/tests/data_preparation/executors/test_cloud_streaming_removed.py` | 제거된 YAML sink가 있을 때 source factory·custom Python source 초기화가 시작되지 않는지 검증 |
| `docs_refactor/` | 적용 결과·기존 설정 이전 방법·목록 갱신 |

`templates/constants.py`에서 해당 이름을 직접 등록한 항목은 발견하지 못했다. YAML 파일 경로와 프런트엔드 streaming 목록을 함께 정리한다. 범위 밖 수정이 필요하면 이유와 추가 파일을 먼저 보고한다.

## UI 및 기존 파이프라인 동작

- 스트리밍 Data loader에서는 4개, Data exporter에서는 3개 선택지 제거. 화면 배치·커널 선택은 그대로 유지.
- 기존 프로젝트의 YAML 파일·사용자 Python 코드를 자동 삭제하거나 변환하지 않는다. 조회·일반 편집은 보존한다.
- 제거된 기본 템플릿을 직접 지정한 생성 요청은 기존 정책의 클라이언트 오류로 거절한다.
- 사용자가 직접 작성한 YAML 내용은 저장할 수 있으나, 제거된 connector_type은 실행 시 명시적 영어 오류로 거절한다. 저장 단계에서 YAML 내용을 새로 제한하는 기능은 이번 범위가 아니다.
- 실행 전 검증은 표준 YAML connector_type을 대상으로 한다. 사용자 Python 코드의 임의 외부 연결을 분석·차단하는 네트워크 방화벽 기능은 아니다.
- 기존 checkpoint·buffer·데이터는 자동 삭제하거나 다른 메시징 시스템으로 이전하지 않는다.

## 보존 범위

S3/MinIO/Ceph sink, Kafka, RabbitMQ, ActiveMQ, NATS source, MongoDB·InfluxDB 및 내부 SQL/검색 저장소, custom Python streaming source/sink를 유지한다. 보존은 현재 있는 방향의 구현에 한한다.

OpenAI 호환 AI·PySpark·내부 Secrets·원본 3100 환경·Compute 라우팅은 변경하지 않는다. SDK 의존성 선언·패키지 uninstall·이미지 재빌드, 기타 SaaS 및 dbt 어댑터 정리는 이번 범위가 아니다.

## 검증 계획

1. 기존 68개 회귀 및 보존 streaming factory 테스트, 신규 사전 검증 테스트.
2. 삭제 파일을 import하는 실행 코드·테스트, 활성 템플릿·UI 등록 잔존 검색.
3. 제거된 source/sink의 SDK 초기화 이전 거절과 내부 브로커 factory·S3 경로 보존 검증. 실제 사내 브로커 연결을 검증한 것으로 보고하지 않음.
4. 격리 streaming 프로젝트의 기존·신형 UI에서 loader/exporter 목록 검증. API 기본 템플릿 직접 요청 거절 및 기존 YAML 조회·편집·실행 오류 검증.
5. TypeScript·Python 구문·diff 검사, 격리 백엔드 외부 연결 감사.
6. 정상 로컬 파이프라인·개발 서버 응답 확인 및 결과 문서 작성. 코드·주석·오류 메시지는 영어 사용.

## 승인 요청

위 21개 파일 삭제와 공통 코드·UI·사전 검증 변경을 검토받은 후 구현한다. 현재 단계에서는 이 변경안 문서만 작성했다.
