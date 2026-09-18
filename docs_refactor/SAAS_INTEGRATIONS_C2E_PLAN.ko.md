# C2e 잔여 SaaS integration 제거안 — 승인 후 적용

2026-09-18. 사용자 요청에 따라 23개 source 및 Salesforce destination의 전용 파일·공유 참조·UI·의존성을 조사했다. 사용자 승인 후 적용했다. C2d 체크포인트는 `ce9a32992`이며 [결과와 기존 이미지 오류](SAAS_INTEGRATIONS_C2E_REMOVAL.ko.md)를 참고한다. 아래는 승인 당시 범위다.

## 적용 범위

Amplitude, Chargebee, Commercetools, Datadog, DynamoDB, Facebook Ads, Freshdesk, Front, HubSpot, Intercom, Knowi, LinkedIn Ads, Monday, Mode, Outreach, Paystack, Pipedrive, Postmark, PowerBI, Salesforce, Stripe, Twitter Ads, Zendesk의 source와 Salesforce destination을 제거 대상으로 제안한다.

판단 기준은 이 fork의 현재 integration 구현이다. 제품 이름만으로 해당 제품의 모든 배포 방식이 외부 전용이라고 단정하지 않는다. 현재 내부 endpoint 보존 대상으로 분리한 GitHub·Tableau·Dremio 및 내부 DB는 이 목록에 포함하지 않는다. DynamoDB는 현재 client 생성 시 endpoint_url을 전달하지 않으며, S3 호환 저장소와 독립된 경로다.

## 전용 파일 삭제

총 **593개**: Python 257개, JSON 304개, Markdown 25개, 확장자 없는 파일 5개, shell 2개. provider 내부의 테스트·테스트 설정·schemas·README도 포함한다. 정확한 파일은 [전체 목록](SAAS_INTEGRATIONS_C2E_FILES.ko.md)에 기록했다.

| provider | 삭제 파일 수 |
|---|---:|
| `amplitude` | 9 |
| `chargebee` | 50 |
| `commercetools` | 39 |
| `datadog` | 13 |
| `dynamodb` | 3 |
| `facebook_ads` | 41 |
| `freshdesk` | 19 |
| `front` | 32 |
| `hubspot` | 43 |
| `intercom` | 18 |
| `knowi` | 8 |
| `linkedin_ads` | 33 |
| `monday` | 10 |
| `mode` | 10 |
| `outreach` | 27 |
| `paystack` | 10 |
| `pipedrive` | 43 |
| `postmark` | 18 |
| `powerbi` | 12 |
| `salesforce` | 23 |
| `stripe` | 25 |
| `twitter_ads` | 61 |
| `zendesk` | 46 |

Amplitude는 connection 전용 디렉터리 3개 파일을 포함한다. Salesforce는 source와 destination 양쪽 파일을 합산했다. 공통 connection/base·SQL·날짜·HTTP·Singer 유틸리티는 삭제하지 않는다.

## 공통 파일 변경

| 파일 | 적용 내용 |
|---|---|
| `mage_ai/data_integrations/sources/constants.py` | 위 23개 등록 제거 |
| `mage_ai/data_integrations/destinations/constants.py` | Salesforce 등록 제거 |
| `mage_ai/shared/cloud_features.py` | 23개 snake_case 식별자를 제거 정책에 추가. 기존 API·동적 로딩·블록 실행 검증 적용 |
| `mage_integrations/mage_integrations/sources/constants.py` | 삭제 대상 DynamoDB에서만 사용하는 `DATABASE_TYPE_DYNAMODB` 제거 |
| `mage_integrations/mage_integrations/tests/sources/test_base.py` | Intercom/Stripe import 제거. 공통 discover/schema 검증은 로컬 fixture로 대체하여 유지 |
| 신규 `mage_integrations/mage_integrations/tests/sources/samples/schema_discovery/` 아래 JSON fixture 2개 | 외부 서비스와 독립된 최소 스키마로 파일명·필드·discover 결과 검사. 임시 디렉터리 또는 테스트 경로 주입 사용 |
| `mage_ai/tests/data_preparation/test_cloud_connectors_removed.py` | 새 공급자 전체의 API payload·실행·동적 로딩 차단과 보존 카탈로그 검증 확장 |
| `docs_refactor/` | 결과·이전 안내·잔여 목록 갱신 |

공통 Source 테스트의 현재 `list(schemas).sort()` 비교는 양쪽 모두 None을 반환하므로 실제 스키마 목록 검증이 되지 않는다. fixture 전환 시 `sorted(...)`와 실제 스키마 내용 assertion으로 바꿔 원래 검증 목적을 보존한다. 해당 테스트를 통째로 삭제하지 않는다.

프런트엔드의 기존 IntegrationSourceEnum은 metadata 식별용으로 유지한다. 사용처 검색에서 이번 제거 공급자 enum의 활성 분기는 찾지 못했다. UI는 API 카탈로그로 목록을 구성하므로 새로운 화면·레이아웃 변경은 예정하지 않는다.

GitHub sync에 남은 `singer-io/tap-salesforce` 문자열은 GitHub가 다루는 저장소 이름별 처리다. Salesforce 커넥터 import가 아니므로 삭제하지 않는다. SQL/Teradata의 Stripe 스키마 예시 주석, 요일 Monday, 통계 Mode, 그래픽 amplitude도 기능 참조와 구분하여 유지한다.

## UI 및 기존 프로젝트 영향

- Data loader → Sources에서 23개, Data exporter → Destinations에서 Salesforce 제거.
- 코드 등록 목록 기준 source는 37개에서 14개, destination은 15개에서 14개가 남는다. 동적 API가 모듈 로딩 상태에 따라 제외하는 항목이 있을 수 있으므로 실제 응답 수와 보존 항목은 별도로 검증한다.
- 기존 pipeline·block의 조회와 커넥터 외 수정은 유지. 제거된 공급자 설정을 새로 지정하거나 실행·로딩하면 영어 오류 반환.
- 사용자 코드·설정·자격증명·체크포인트·데이터를 자동 삭제하거나 내부 서비스로 이관하지 않는다. 삭제 모듈 직접 import는 ImportError가 발생할 수 있다.
- source/sink 메뉴만 숨기고 구현을 남기는 방식이 아니라 승인된 전용 구현과 카탈로그·실행 진입점을 함께 정리한다.

## 보존 대상

Source: Amazon S3, Api, Couchbase, Doris, Dremio, GitHub, Microsoft SQL Server, MongoDB, MySQL, OracleDB, PostgreSQL, Sftp, Tableau, Teradata.

Destination: Amazon S3, Clickhouse, Delta Lake S3, Doris, Elasticsearch, Kafka, MongoDB, Microsoft SQL Server, MySQL, Opensearch, OracleDB, PostgreSQL, Teradata, Trino.

GitHub의 base_url, Tableau의 base_url, Dremio의 hostname 지원을 확인했다. GitHub의 외부 기본 URL과 각 커넥터의 추가 외부 인증 경로까지 차단되었다는 뜻은 아니다. 내부 전용 설정 강제는 별도 변경안으로 다룬다. S3/MinIO/Ceph, OpenAI 호환 AI, PySpark, 내부 Secrets, 원본 3100 및 Compute 라우팅은 유지한다.

## 패키지 및 남는 외부 기능

- 정적 Python import 검색에서 이번 대상 밖의 stripe·simple_salesforce·facebook_business·twitter_ads·zenpy 직접 import는 발견하지 못했다. 삭제 후 제거 후보이나 선언·설치 의존성과 동적 로딩 검증은 C3에서 수행한다.
- 해당 5개 SDK는 루트 requirements와 integration requirements에 선언되어 있다. 이번에는 선언 삭제·수동 uninstall·이미지 재빌드를 포함하지 않는다.
- boto3/botocore는 S3에서, requests/httpx/Singer는 공통 코드 및 보존 커넥터에서 사용하므로 유지한다.
- **Datadog integration 제거와 별개로 `mage_ai/services/datadog/__init__.py` 및 전용 테스트가 남는다.** 메트릭·이벤트 전송 모듈이며 이번 integration 제거에 임의로 포함하지 않는다. 별도 후속 런타임 정리 대상으로 기록한다. 따라서 이번 작업만으로 모든 외부 통신 기능 제거 완료라고 보고하지 않는다.
- dbt 클라우드 어댑터·기타 잔여 외부 인증/AI 공급자 경로·전체 SDK·이미지 경량화도 별도 검토 대상이다.

## 검증 및 적용 순서

1. 승인 후 기존 C2d 완료분을 먼저 로컬 커밋하고 C2e를 적용한다. GitHub push는 하지 않는다.
2. 593개 전용 파일 삭제와 공통 등록·정책·테스트 fixture 변경. 삭제 모듈/스키마/설정 참조 전수 검색.
3. 기존 79개 회귀 및 integration 공통 Source 테스트 실행. 삭제 provider 내부 테스트를 공통 회귀로 계산하지 않음.
4. 격리 API에서 전체 제거 목록 미노출, 직접 생성·동적 source/destination 로딩이 연결 전에 거절되는지 검사. 보존 목록 확인.
5. 실제 Sources/Destinations UI 검사. 대표 legacy source 및 Salesforce destination의 조회·일반 수정·실행 오류 확인.
6. 실제 로컬 pipeline 실행, S3/AI/Spark 설정 회귀, TypeScript·Python 구문·diff 검사, 격리 백엔드 외부 연결 감사.
7. 결과 문서화 및 개발 서버 반영. 실제 사내 endpoint·브로커 연결이나 이미지 크기 감소를 검증한 것으로 보고하지 않는다.

## 승인 요청 범위

C2d 선행 로컬 커밋, 위 593개 파일 제거, 공통 등록·제거 정책·독립 fixture 전환 및 검증·문서화. 승인 전에는 문서 준비 외 구현·커밋·재시작을 진행하지 않는다. 코드·주석·오류 메시지는 영어로 작성한다. 추가 수정 파일이 필요하면 이유와 범위를 먼저 보고한다.
