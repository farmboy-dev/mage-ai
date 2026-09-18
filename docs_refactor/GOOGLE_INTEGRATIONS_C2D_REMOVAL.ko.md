# C2d Google integration 제거 결과

2026-09-18. [승인안](GOOGLE_INTEGRATIONS_C2D_PLAN.ko.md)에 따라 적용했다. 이전 체크포인트는 `682a1e580`이며 C2d 구현은 이후 `ce9a32992`로 커밋했다. GitHub push는 하지 않았다.

## 적용 내용

- Google Ads·Google Analytics·Google Search Console source와 전용 connection의 구현·스키마·설정·문서 등 32개 파일 삭제.
- 이 connection에서만 import하던 `connections/utils/google.py` 삭제. 총 삭제 파일 33개.
- 공통 source 카탈로그에서 세 공급자 제거. API를 사용하는 integration 선택 UI에 반영했으며 JSX·레이아웃은 변경하지 않음.
- 제거 정책에 세 식별자를 추가해 직접 API 요청·블록 실행·동적 integration 로딩을 연결 전에 거절.
- 기존 프런트엔드 enum은 메타데이터 식별용으로 유지. 사용자 프로젝트·자격증명·작성 코드를 자동 삭제하지 않음.
- 테스트의 공급자 검증 범위를 확장하고 내부 API·SFTP·PostgreSQL·S3 카탈로그 보존을 확인.

## 검증 결과

| 항목 | 결과 |
|---|---|
| Python 회귀 | 79개 통과. 새 Google 공급자들을 기존 parameter loop에 추가하여 검증 |
| TypeScript·구문·diff | 전체 TypeScript 및 변경 Python 구문, diff 검사 통과 |
| 잔존 import | 삭제한 source/connection/helper를 import하는 Python 코드·테스트 검색 결과 없음 |
| API 목록 | integration source 39개 → 36개. 제거된 3개 미노출, S3·API·SFTP·PostgreSQL 유지 |
| 직접 생성 | 3개 공급자 설정 요청 모두 `error.code=400`, 블록 저장 없음 |
| 기존 설정 | 격리 프로젝트에 legacy 설정을 넣은 pipeline 3개를 생성하여 조회·커넥터 외 속성 수정 통과 |
| 실행·로딩 | 실제 legacy block의 execute_sync 및 integration module 로딩에서 영어 제거 오류 발생 |
| UI | 신형 블록 메뉴의 Sources 하위 목록에서 Google 3개 미노출, Amazon S3·PostgreSQL 표시, JavaScript 오류 0개 |
| 로컬 실행 | 실제 loader→transformer→exporter 실행 및 결과 `[2, 4, 6]` 확인 |
| 외부 연결 | 격리 백엔드 감사 기록에 외부 연결 시도 없음 |
| 개발 서버 | 재시작 후 API 응답 확인, 3000 개발 UI에 반영 |

[Sources 메뉴 화면](google_integrations_c2d/sources.png).

로그: `/tmp/mage-c2d-tests.log`, `/tmp/mage-c2d-tsc.log`, `/tmp/mage-c2d-browser.log`, `/tmp/mage-c2d-browser.json`, `/tmp/mage-c2d-pipeline.log`. 격리 프로젝트에서만 테스트했고 실제 사용자 프로젝트는 검증용으로 수정하지 않았다.

## 기존 프로젝트 이전 및 남은 범위

기존 pipeline 조회·일반 수정은 가능하지만 세 Google integration을 지정하거나 실행하면 오류가 발생한다. 삭제된 모듈을 직접 import하는 사용자 코드는 ImportError가 발생할 수 있다. 필요한 데이터를 내부 파일·DB·API로 별도 확보한 뒤 지원되는 커넥터로 이전해야 한다. 자동 데이터 이관은 제공하지 않는다.

S3/MinIO/Ceph, 내부 DB·API·SFTP, 내부 메시징, OpenAI 호환 AI, PySpark, Mage Secrets를 유지했다. 실제 사내 endpoint 연결·Spark 연산 검증을 새로 수행한 것은 아니다. 원본 3100 환경과 Compute 라우팅은 변경하지 않았다.

Google SDK 의존성 선언과 실행 이미지의 설치 패키지는 아직 남아 있다. 이미지 크기 감소는 검증하지 않았다. 나머지 SaaS integrations·dbt 클라우드 어댑터·C3 의존성 및 이미지 정리는 후속 승인 대상이다.
