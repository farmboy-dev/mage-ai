# Sources / Destinations 잔여 항목 확인

후속 상태: 이 문서의 23개 source 및 Salesforce destination은 이후 C2e에서 제거했다. [적용 결과와 남은 이미지 호환성 문제](SAAS_INTEGRATIONS_C2E_REMOVAL.ko.md)를 참고한다. 아래는 제거 전 조사 기록이다.

2026-09-18. 실행 중인 3000 포트의 example_pipeline 편집 화면에서 Data loader → Sources, Data exporter → Destinations 메뉴를 직접 열어 확인했다. 프로젝트 설정·블록·애플리케이션 코드는 변경하지 않았다.

## 확인 결과

남은 외부 서비스가 실제로 등록되어 있다. 삭제한 Google Ads·Analytics·Search Console는 표시되지 않았다. 현재 현상은 이전 삭제 항목의 캐시 재노출이 아니라 아직 제거 범위에 넣지 않은 공급자 등록이다. 전체 외부 서비스 제거는 완료되지 않았다.

### Source 후속 제거 검토 대상

Amplitude, Chargebee, Commercetools, Datadog, DynamoDB, Facebook Ads, Freshdesk, Front, HubSpot, Intercom, Knowi, LinkedIn Ads, Monday, Mode, Outreach, Paystack, Pipedrive, Postmark, PowerBI, Salesforce, Stripe, Twitter Ads, Zendesk.

이 23개는 다음 전체 사용 경로·전용 파일 조사 대상으로 분류했다. 이 문서는 개별 제품의 모든 배포 방식에 대한 단정이나 삭제 승인이 아니다. 특히 현재 구현을 기준으로 내부 endpoint 사용 여부를 검토해야 한다.

코드에서 추가 확인한 사항:

- PowerBI client: `https://api.powerbi.com/v1.0/myorg` 고정.
- Knowi client: `https://knowi.com/api/1.0` 고정.
- Mode client: `https://app.mode.com/api/{workspace}` 사용.
- DynamoDB source: boto3 DynamoDB client 생성 시 endpoint_url 인자를 전달하지 않음.

### Destination

Salesforce가 남아 있으며 source와 destination 양쪽 제거 검토 대상이다. 실제 구현은 simple_salesforce 및 Salesforce 인증 모듈을 사용한다.

Amazon S3·Delta Lake S3는 MinIO/Ceph 사용을 위해 보존 대상이다. ClickHouse·Doris·Elasticsearch·Kafka·MongoDB·Microsoft SQL Server·MySQL·OpenSearch·OracleDB·PostgreSQL·Teradata·Trino는 클라우드 이름처럼 보이는지 여부로 삭제하지 않고 내부 연결을 보존한다.

### 별도 판단 대상

- GitHub: client가 config.base_url을 지원하며 미설정 시 `https://api.github.com`을 사용. 내부 URL 지원과 외부 기본값 제거를 함께 검토해야 한다.
- Tableau: 사용자 base_url을 client로 전달. 내부 서버 연결 여부를 고려하여 보존 판단.
- Dremio: connection의 hostname 설정 지원. 내부 서비스 연결 대상으로 유지 검토.
- Couchbase·MongoDB·일반 API·SFTP·내부 SQL은 외부 SaaS 일괄 삭제 범위로 취급하지 않는다.

## 다음 작업 제안

23개 source와 Salesforce destination을 한 번에 목록화하고, 공유 모듈·의존성·UI 및 오류 처리 범위를 정리하여 승인받는다. GitHub·Tableau·Dremio는 내부 endpoint 지원을 별도 확인한다. 승인 전 코드 삭제나 메뉴 숨김을 적용하지 않는다.

근거 파일: `mage_ai/data_integrations/sources/constants.py`, `mage_ai/data_integrations/destinations/constants.py`, `mage_integrations/mage_integrations/sources/*`, `mage_integrations/mage_integrations/connections/dremio/__init__.py`, `mage_integrations/mage_integrations/destinations/salesforce/__init__.py`.

화면 검사 기록: `/tmp/mage-integration-inventory.json`, `/tmp/mage-inventory-Sources.png`, `/tmp/mage-inventory-Destinations.png`. 로그인 상태는 파일로 저장하지 않았다.
