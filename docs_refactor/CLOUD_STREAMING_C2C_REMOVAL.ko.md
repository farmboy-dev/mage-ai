# C2c 클라우드 스트리밍 제거 결과

2026-09-18. [승인안](CLOUD_STREAMING_C2C_PLAN.ko.md)에 따라 적용했다. 이전 C2b 체크포인트는 `04836802d`다. 이번 C2c 변경은 아직 커밋하지 않았으며 GitHub push는 하지 않았다.

## 변경 내용

- SQS·Kinesis·Google Pub/Sub·Azure Event Hub source 4개와 Kinesis·Google Pub/Sub·Azure Data Lake sink 3개 제거.
- 전용 구현 7개, YAML 템플릿 7개, 전용 테스트 7개 등 승인된 파일 21개 삭제.
- source/sink factory의 해당 분기·import 제거. 제거 정책에 공급자 식별자 5개 추가하여 직접 factory 및 기존 API·템플릿 검증에 적용.
- 스트리밍 loader/exporter UI 목록과 표시 이름 매핑 정리. 기존 enum 식별자는 메타데이터 호환을 위해 유지.
- 실행기에서 모든 YAML source/sink 설정을 먼저 변수 치환·정책 검사하고 재사용. 제거된 sink가 있으면 YAML source뿐 아니라 custom Python source 초기화도 시작하지 않음.
- SourceFactory 테스트의 삭제된 공급자 import 및 성공 기대 제거. 신규 실행기 테스트에 source/sink 직접 거절과 사전 검증을 함께 추가했다. SinkFactory 기존 테스트는 수정 없이 보존 회귀에 포함했다.

## 검증 결과

- Python 회귀 78개 통과 후 정상 배치 전달 검증 1개를 추가하고 실행기 테스트 4개를 재실행하여 통과. 중복 제외 총 79개 검증 통과.
- 제거된 source/sink가 SDK import 전에 거절되는지, 제거된 sink가 있을 때 모든 source 초기화가 생략되는지 검증. 변수 치환으로 결정되는 connector_type도 포함.
- 보존 YAML source→sink의 배치 전달과 설정별 1회 치환을 mock으로 검증. 실제 Kafka/RabbitMQ 브로커 연결 검증은 아니다.
- 전체 TypeScript, 변경 Python 구문, `git diff --check` 통과. 삭제 모듈을 import하는 Python 실행 코드·테스트 잔존 검색 결과 없음.
- 격리 streaming 프로젝트에서 UI feature flag를 false/true로 바꾸어 loader/exporter 메뉴 4가지 확인. 제거 대상 미노출, Kafka 및 exporter의 Amazon S3 유지, JavaScript 오류 0개. 스트리밍 화면에서 실제 표시되는 메뉴를 검사했다.
- 5개 공급자 기본 템플릿 직접 생성 API가 모두 `error.code=400` 반환. 실패한 블록은 저장되지 않음.
- 격리 프로젝트에서 제거된 connector_type을 가진 사용자 YAML 생성·수정·파이프라인 조회 통과. 저장된 YAML을 실제 SourceFactory에 전달하면 명시적 제거 오류 발생.
- 실제 로컬 loader→transformer→exporter 실행 및 결과 `[2, 4, 6]` 확인.
- 격리 백엔드 외부 연결 시도 기록 없음. 개발 서버 재시작 및 API 응답 확인.

화면: [loader](cloud_streaming_c2c/loader.png), [exporter](cloud_streaming_c2c/exporter.png).

상세 로그: `/tmp/mage-c2c-tests.log`, `/tmp/mage-c2c-preflight.log`, `/tmp/mage-c2c-tsc.log`, `/tmp/mage-c2c-browser.log`, `/tmp/mage-c2c-browser.json`, `/tmp/mage-c2c-pipeline.log`.

## 기존 프로젝트 및 보존 범위

사용자 YAML·Python 코드와 checkpoint·buffer는 자동 삭제·이관하지 않았다. 기존 YAML 조회·편집은 가능하지만 제거된 커넥터는 실행 전에 오류가 발생한다. 삭제 모듈을 직접 import하는 사용자 코드는 ImportError가 발생할 수 있다. 사용자 Python 코드의 임의 외부 연결을 차단하는 네트워크 방화벽 기능은 아니다.

S3/MinIO/Ceph sink, Kafka·RabbitMQ·ActiveMQ·NATS source, 내부 DB·검색 저장소, custom Python streaming을 기존 지원 방향대로 보존했다. OpenAI 호환 AI·PySpark·내부 Secrets와 원본 3100 환경은 변경하지 않았다. 실제 사내 서비스 연결·Spark 연산을 새로 검증한 것은 아니다.

SDK 설치 패키지 및 이미지 크기는 이번에 변경하지 않았다. 남은 SaaS integrations·dbt 클라우드 어댑터·C3 의존성 및 이미지 경량화는 별도 승인 대상이다.
