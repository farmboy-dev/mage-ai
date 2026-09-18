# C2e 잔여 SaaS integration 제거 결과

2026-09-18. [승인안](SAAS_INTEGRATIONS_C2E_PLAN.ko.md)에 따라 적용했다. C2d 완료분과 검토 문서는 먼저 `ce9a32992`로 로컬 커밋했다. C2e 및 Tableau·Teradata 추가 변경은 이후 `d0d25e265`로 커밋했으며 GitHub push는 하지 않았다.

후속 갱신: 사용자 요청으로 Tableau·Teradata도 추가 제거했다. [추가 결과](TABLEAU_TERADATA_REMOVAL.ko.md)를 참고한다. 아래는 C2e 최초 완료 기록이다.

## 적용 내용

- 승인된 23개 source와 Salesforce destination의 전용 파일 **593개** 삭제. [전체 목록](SAAS_INTEGRATIONS_C2E_FILES.ko.md)과 실제 Git 삭제 수 일치.
- 공통 source/destination 등록과 DynamoDB 전용 상수 정리. 제거 정책에 23개 식별자를 추가해 직접 생성·동적 로딩·실행 전에 차단.
- Intercom·Stripe에 의존하던 공통 Source 테스트를 SchemaFixtureSource와 로컬 JSON fixture 2개로 전환. discover 결과·필터링·스키마 이름과 필드 내용을 검증. `sort()` 반환값 None 비교를 `sorted()`로 교체.
- Sources/Destinations 목록은 API 등록 변경으로 반영. JSX·화면 배치·커널 선택은 변경하지 않음.
- 기존 enum 식별자·GitHub 저장소별 호환 문자열·일반 단어가 포함된 코드와 주석은 유지.

## 검증 결과

| 항목 | 결과 |
|---|---|
| Python | 기존 79개 및 integration 공통 Source 17개, 총 **96개 통과**. 제거 대상 전체를 기존 loop에 추가하여 검증 |
| TypeScript | 전체 검사 통과 |
| 정적 검사 | Python 구문·diff 검사 통과. 삭제한 integration namespace의 Python 참조 검색 결과 없음 |
| UI | 실제 Sources 14개·Destinations 14개 표시, 제거 대상 미노출, JavaScript 오류 0개 |
| 상세 API | source 13개·destination 13개 반환. 아래 기존 이미지 오류 2건으로 UI 등록 수와 차이 발생 |
| 직접 생성 | 23개 source와 Salesforce destination 요청 모두 `error.code=400`. 거절된 source 블록 저장 없음 |
| 동적 로딩 | 제거된 source 23개 및 Salesforce destination 로딩이 명시적 오류로 거절됨 |
| 기존 설정 | 격리 프로젝트의 Amplitude·Stripe source 및 Salesforce destination 설정 조회·일반 수정 통과, 실제 block 실행은 연결 전에 거절 |
| 정상 로컬 실행 | loader→transformer→exporter 실제 실행, 결과 `[2, 4, 6]` 확인 |
| 외부 연결 | 격리 백엔드 감사 기록에 외부 연결 시도 없음 |
| 개발 서버 | 재시작 후 API 응답 확인. 원본 3100 환경은 변경하지 않음 |

화면: [Sources](saas_integrations_c2e/sources.png), [Destinations](saas_integrations_c2e/destinations.png).

로그: `/tmp/mage-c2e-tests.log`, `/tmp/mage-c2e-tsc.log`, `/tmp/mage-c2e-browser.log`, `/tmp/mage-c2e-browser.json`, `/tmp/mage-c2e-pipeline.log`. 사용자 프로젝트는 검증 목적으로 변경하지 않았다.

## 발견한 기존 이미지 문제 — 후속 검토 필요

보존 대상의 상세 API 로딩 중 다음 오류를 발견했다.

1. **Couchbase source**: 설치 SDK가 `libssl.so.1.1`을 찾지 못함.
2. **Delta Lake S3 destination**: 현재 deltalake 패키지에서 `deltalake._internal.PyDeltaTableError`를 import할 수 없음.

UI 카탈로그에는 두 항목이 남지만, 실제 모듈을 import하여 상세 정보를 제공하는 API는 실패한 항목을 제외한다. 따라서 목록 보존을 실제 실행 가능성 검증으로 해석하면 안 된다.

원인 구분을 위해 `git archive HEAD`로 C2e 적용 전 `ce9a32992`의 mage_integrations 코드를 격리 컨테이너의 별도 경로에 추출하고 해당 경로를 우선 PYTHONPATH로 지정하여 import했다. **두 오류 모두 이전 커밋에서도 동일하게 재현**했다. C2e 삭제로 새로 생긴 문제는 아니며, 이번 승인 범위 밖의 패키지·Delta Lake 공통 코드 변경은 하지 않았다. 이전 단계에서 기록한 API 전체 정상 여부는 이 한계를 함께 참고해야 한다.

다음 승인안의 우선 후보는 위 2건의 호환성 보완이다. 전체 이미지 재빌드·SDK 정리 계획과 연계하되 S3 기능을 제거하는 방식으로 해결하지 않는다.

## 남은 범위와 이전 안내

- 기존 사용자 코드·설정·체크포인트·데이터를 자동 삭제·이관하지 않았다. 제거된 커넥터 지정·실행은 오류이며 직접 모듈 import는 ImportError가 발생할 수 있다.
- S3/MinIO/Ceph, 내부 DB·API·SFTP, GitHub·Tableau·Dremio, 내부 메시징, AI·PySpark·Mage Secrets를 유지했다. 실제 사내 endpoint 연결·Spark 연산을 새로 검증한 것은 아니다.
- `mage_ai/services/datadog/` metrics·이벤트 전송은 integration과 별개로 남아 있다. GitHub 등의 외부 기본 URL과 나머지 외부 경로도 후속 검토 대상이다.
- SDK 의존성 선언·설치 패키지와 이미지 크기는 변경하지 않았다. C3에서 별도 정리·검증한다. 모든 외부 통신 기능 제거 완료 상태는 아니다.
