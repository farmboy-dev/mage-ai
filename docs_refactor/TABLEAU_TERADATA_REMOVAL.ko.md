# Tableau·Teradata 추가 제거 결과

2026-09-18. 사용자의 직접 제거 요청에 따라 C2e 후속 변경으로 적용했다. C2e와 이번 변경은 아직 미커밋이며 GitHub push는 하지 않았다.

## 변경

- Tableau source와 Teradata source·destination·connection 전용 파일 16개 삭제.
- 공통 source/destination 카탈로그에서 제거. 제거 정책에 `tableau`, `teradata`를 추가하여 직접 요청·동적 로딩·기존 설정 실행을 연결 전에 차단.
- UI 목록에서 함께 제거되며 JSX·레이아웃은 변경하지 않음. 사용자 프로젝트·데이터·자격증명을 자동 삭제·이관하지 않음.
- SDK 설치 패키지와 requirements의 teradatasql 선언은 기존 C3 계획에 따라 후속 정리 대상으로 유지. 기존 upstream docs 문서는 이번 범위에서 수정하지 않았으며 현재 지원 여부는 docs_refactor 결과를 기준으로 한다.

## 검증

- 기존 Python 회귀와 integration 공통 Source 테스트 총 **96개 통과**. 제거 정책 테스트 loop에서 Tableau·Teradata도 검증.
- 두 source 및 Teradata destination 직접 생성 API는 `error.code=400`. 동적 로딩도 import 전에 명시적 오류.
- 실제 UI의 Sources와 Destinations에서 두 이름 미노출, S3·내부 DB·GitHub 유지. JavaScript 오류 0개.
- 등록/UI 목록은 source 12개·destination 13개. 상세 API는 source 11개·destination 12개로, 기존 Couchbase 및 Delta Lake S3 이미지 오류 때문에 각각 1개씩 제외된다. [기존 문제 분석](SAAS_INTEGRATIONS_C2E_REMOVAL.ko.md) 참고.
- 삭제 모듈 import 잔존 없음. 변경 Python 구문 및 diff 검사 통과. 프런트엔드 소스 변경이 없어 TypeScript 검사는 반복하지 않음.
- 격리 백엔드 외부 연결 시도 기록 없음. 개발 서버 재시작 후 API 응답 확인.

로그: `/tmp/mage-tableau-teradata-tests.log`, `/tmp/mage-tableau-teradata-browser.log`, `/tmp/mage-tableau-teradata-browser.json`.

## 삭제 파일

- `mage_integrations/mage_integrations/connections/teradata/__init__.py`
- `mage_integrations/mage_integrations/destinations/teradata/README.md`
- `mage_integrations/mage_integrations/destinations/teradata/__init__.py`
- `mage_integrations/mage_integrations/destinations/teradata/templates/config.json`
- `mage_integrations/mage_integrations/destinations/teradata/utils.py`
- `mage_integrations/mage_integrations/sources/tableau/README.md`
- `mage_integrations/mage_integrations/sources/tableau/__init__.py`
- `mage_integrations/mage_integrations/sources/tableau/client.py`
- `mage_integrations/mage_integrations/sources/tableau/schema.py`
- `mage_integrations/mage_integrations/sources/tableau/schemas/views.json`
- `mage_integrations/mage_integrations/sources/tableau/schemas/workbooks.json`
- `mage_integrations/mage_integrations/sources/tableau/streams.py`
- `mage_integrations/mage_integrations/sources/tableau/templates/config.json`
- `mage_integrations/mage_integrations/sources/teradata/README.md`
- `mage_integrations/mage_integrations/sources/teradata/__init__.py`
- `mage_integrations/mage_integrations/sources/teradata/templates/config.json`
