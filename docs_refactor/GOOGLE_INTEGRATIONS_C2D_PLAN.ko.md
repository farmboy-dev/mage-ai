# C2d Google 마케팅·분석 integration 제거안 — 승인 후 적용

2026-09-18. C2c를 로컬 커밋 `682a1e580`에 저장한 후 준비했다. 사용자 승인 후 적용했다. [결과](GOOGLE_INTEGRATIONS_C2D_REMOVAL.ko.md)를 참고한다. 아래는 승인 당시의 계획이다. GitHub push는 하지 않았다.

## 제안 범위와 근거

Google Ads, Google Analytics, Google Search Console source integration을 제거한다. 로컬 코드에서 각각 GoogleAdsClient, BetaAnalyticsDataClient, googleapiclient의 webmasters API를 사용하는 것을 확인했다. 이 변경은 일반 내부 HTTP API 커넥터 제거를 의미하지 않는다.

전용 source 3개 디렉터리와 connection 2개 디렉터리의 추적 파일 32개, 해당 connection에서만 import하는 `connections/utils/google.py` 1개를 삭제 대상으로 제안한다. 구현·스키마·템플릿·전용 문서를 포함한다.

## 삭제 대상 33개

- `mage_integrations/mage_integrations/connections/google_analytics/README.md`
- `mage_integrations/mage_integrations/connections/google_analytics/__init__.py`
- `mage_integrations/mage_integrations/connections/google_analytics/constants.py`
- `mage_integrations/mage_integrations/connections/google_analytics/utils.py`
- `mage_integrations/mage_integrations/connections/google_search_console/__init__.py`
- `mage_integrations/mage_integrations/sources/google_ads/README.md`
- `mage_integrations/mage_integrations/sources/google_ads/__init__.py`
- `mage_integrations/mage_integrations/sources/google_ads/tap_google_ads/__init__.py`
- `mage_integrations/mage_integrations/sources/google_ads/tap_google_ads/client.py`
- `mage_integrations/mage_integrations/sources/google_ads/tap_google_ads/discover.py`
- `mage_integrations/mage_integrations/sources/google_ads/tap_google_ads/report_definitions.py`
- `mage_integrations/mage_integrations/sources/google_ads/tap_google_ads/schemas/accounts.json`
- `mage_integrations/mage_integrations/sources/google_ads/tap_google_ads/schemas/ad_groups.json`
- `mage_integrations/mage_integrations/sources/google_ads/tap_google_ads/schemas/ads.json`
- `mage_integrations/mage_integrations/sources/google_ads/tap_google_ads/schemas/campaigns.json`
- `mage_integrations/mage_integrations/sources/google_ads/tap_google_ads/streams.py`
- `mage_integrations/mage_integrations/sources/google_ads/tap_google_ads/sync.py`
- `mage_integrations/mage_integrations/sources/google_ads/tap_google_ads/tests/base.py`
- `mage_integrations/mage_integrations/sources/google_ads/templates/config.json`
- `mage_integrations/mage_integrations/sources/google_analytics/README.md`
- `mage_integrations/mage_integrations/sources/google_analytics/__init__.py`
- `mage_integrations/mage_integrations/sources/google_analytics/templates/config.json`
- `mage_integrations/mage_integrations/sources/google_search_console/README.md`
- `mage_integrations/mage_integrations/sources/google_search_console/__init__.py`
- `mage_integrations/mage_integrations/sources/google_search_console/schemas/performance_report_country.json`
- `mage_integrations/mage_integrations/sources/google_search_console/schemas/performance_report_custom.json`
- `mage_integrations/mage_integrations/sources/google_search_console/schemas/performance_report_date.json`
- `mage_integrations/mage_integrations/sources/google_search_console/schemas/performance_report_device.json`
- `mage_integrations/mage_integrations/sources/google_search_console/schemas/performance_report_page.json`
- `mage_integrations/mage_integrations/sources/google_search_console/schemas/performance_report_query.json`
- `mage_integrations/mage_integrations/sources/google_search_console/streams.py`
- `mage_integrations/mage_integrations/sources/google_search_console/templates/config.json`
- `mage_integrations/mage_integrations/connections/utils/google.py`

## 공통 코드 및 UI

| 파일 | 변경 내용 |
|---|---|
| `mage_ai/data_integrations/sources/constants.py` | 세 source 등록 제거. API를 사용하는 integration 선택 UI에 반영 |
| `mage_ai/shared/cloud_features.py` | `google_ads`, `google_analytics`, `google_search_console`을 제거 집합에 추가. 직접 요청·동적 import·기존 설정 실행 차단 |
| `mage_ai/tests/data_preparation/test_cloud_connectors_removed.py` | 새 제거 대상의 카탈로그·API payload·동적 로딩 차단, 기존 프로젝트 및 보존 목록 검증 확장 |
| `docs_refactor/` | 적용 결과·이전 방법·인덱스 갱신 |

프런트엔드 IntegrationSourceEnum의 Google Ads/Search Console 식별자는 기존 메타데이터 호환용으로 유지한다. 이번 조사에서 이 3개 공급자의 별도 일반 I/O 기본 템플릿은 발견하지 못했다. UI 배치나 커널 선택을 바꾸지 않고 API source 목록에서 제거한다. 추가 수정 경로가 필요하면 적용 전에 보고한다.

## 기존 프로젝트 동작

기존 pipeline·block·사용자 코드와 설정 파일을 자동 삭제하지 않는다. 조회·커넥터 외 필드 수정은 유지한다. 제거된 integration을 새로 지정하거나 source를 로딩·실행하면 연결 전에 영어 오류로 거절한다. 삭제 모듈을 직접 import하는 사용자 코드는 ImportError가 발생할 수 있다. 해당 데이터가 필요하면 별도로 확보한 내부 파일·DB·API를 사용하도록 이전해야 하며 자동 대체는 하지 않는다.

## 의존성 및 제외 범위

현재 `mage_integrations/requirements.txt`에 google-ads, google-analytics-data, google-api-python-client가 남아 있다. 루트 requirements에도 Google API·Analytics 패키지가 존재한다. 이번 단계에서는 공급자 구현과 사용 경로를 먼저 제거하며 의존성 선언·이미지 정리는 C3에서 일괄 검증한다. 수동 uninstall이나 이미지 크기 감소를 포함하지 않는다.

S3/MinIO/Ceph, 내부 DB·API·SFTP, Kafka 및 기존 내부 메시징, OpenAI 호환 AI, PySpark, Mage Secrets를 유지한다. 원본 3100 환경과 Compute 라우팅도 변경하지 않는다.

Facebook/LinkedIn/Twitter Ads, Salesforce 등 나머지 외부 서비스는 이번 범위 밖이다. GitHub Enterprise·Tableau Server 등 내부 설치 가능성이 있는 제품은 이름만으로 일괄 삭제하지 않고 현재 구현의 endpoint 지원을 조사한 뒤 별도 제안한다.

## 검증 계획

1. 기존 회귀 79개 및 새 공급자 차단 검증. 삭제 모듈 import·스키마 경로·활성 등록 잔존 검색.
2. 격리 API에서 source 목록의 세 항목 제거 및 직접 생성·로딩 요청 차단 확인. S3·내부 DB·API·SFTP 보존 확인.
3. 실제 integration 선택 UI에서 세 항목 미노출과 보존 항목 표시 확인. 기존 pipeline 조회·일반 수정 및 실행 오류 검증.
4. Python 구문, TypeScript, diff 검사 및 격리 백엔드 외부 연결 감사.
5. 정상 로컬 pipeline 실행과 개발 서버 응답 확인. 실제 Google 서비스에 접속하지 않는다.

## 검토 요청

위 전용 파일 33개 삭제, 공통 source 등록·제거 정책·검증·문서 변경을 승인받은 뒤 구현한다. 코드·주석·오류 메시지는 영어로 작성한다.
