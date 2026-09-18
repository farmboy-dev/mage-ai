# C2a Algolia·Airtable 제거 결과

2026-09-18. [파일별 변경안](ALGOLIA_AIRTABLE_REMOVAL_PLAN.ko.md)에 대한 사용자 승인 후 적용했다. 이전 체크포인트는 `b49f9c837`이며 C2a 변경은 이후 `6a28ea7db`로 커밋했다. GitHub push는 하지 않았다.

## 적용 내용

- 승인된 전용 파일 12개 삭제: I/O 2개, 기본 템플릿 3개, Airtable integration connection/source/destination 및 설정·문서 7개.
- Algolia loader/exporter와 Airtable loader 기본 등록, Airtable integration source/destination 등록 제거.
- 전용 ConfigKey·VerboseConfigKey·매핑, 신규 프로젝트 설정 예시, `map_json_to_airtable` 제거.
- `requirements.txt`의 `pyairtable` 선언 2개와 `setup.py`의 `airtable` extra 및 `all` 의존성 제거. 신규 설치에서 `mage-ai[airtable]` extra를 제공하지 않는다.
- 기존 제거 정책에 `algolia`, `airtable` 추가. 직접 블록 생성·실행·integration 로딩·기본 템플릿 검색 캐시에서 공통 차단 적용.
- 기존 메타데이터 식별용 DataSource enum과 UI Browser mock 경로는 승인안대로 유지. 사용자 코드·프로젝트 설정·사용자 템플릿을 자동 삭제하지 않았다.
- 사용자 코드가 삭제된 모듈을 직접 import하면 ImportError가 발생할 수 있다. 해당 코드는 사용자가 지원하는 커넥터로 이전해야 한다.

## 검증 결과

| 검증 | 결과 |
|---|---|
| Python 회귀 검증 | 58개 통과. 템플릿, 제거 정책, stale cache, S3 호환, OpenAI 호환, Spark 커널·UI 설정, 실행기 정책 포함 |
| TypeScript | 전체 `yarn tsc --noEmit` 통과 |
| 정적 검사 | 변경 Python 구문 검사, `git diff --check` 통과 |
| 격리 API 카탈로그 | SQL provider 9개, source 39개, destination 14개. 제거 대상 미노출, S3·PostgreSQL·Spark 유지 |
| 직접 블록 요청 | Airtable data_source, Algolia data_provider, Algolia template_path 요청 모두 `error.code=400`; 블록 저장 없음 |
| 기존 프로젝트 | 격리 프로젝트에 두 서비스의 legacy 파이프라인 생성 후 조회·일반 속성 수정 통과, 기존 커넥터 설정 유지 |
| 실행 차단 | 단위 테스트에서 두 서비스의 블록 실행·integration 로딩을 실제 연결 전에 거절 |
| UI | 기존·신형 Data loader 메뉴와 Databases 하위 메뉴에서 두 서비스 미노출; Amazon S3 유지; JavaScript 오류 0개 |
| Browse templates | 신형 UI에서 정상 진입. 이 화면은 사용자 템플릿 목록이며 격리 프로젝트는 0개. 기본 커넥터 카탈로그 보존 검증과 구분 |
| 외부 연결 | 격리 백엔드 감사 로그에 외부 연결 시도 없음 |
| 개발 서버 | 소스 반영 후 재시작, 6789 API HTTP 200 확인. 3000 개발 UI에서 사용 가능 |

검증 중 소스 저장에 따른 격리 서버 자동 재시작으로 첫 브라우저 요청이 끊어졌다. 서버 기동 후 재실행하여 통과했다. Browse templates를 기본 카탈로그로 가정한 초기 검증은 실제 사용자 템플릿 API를 확인한 뒤 정상적인 빈 목록을 허용하도록 수정했다.

화면 기록: [기존 메뉴의 Databases](algolia_airtable/menu-v1.png), [신형 Browse templates](algolia_airtable/browse-templates-v2.png).

로컬 상세 로그: `/tmp/mage-c2a-tests.log`, `/tmp/mage-c2a-tsc.log`, `/tmp/mage-c2a-browser.json`. 임시 감사 컨테이너는 검증 후 삭제했다.

## 보존 범위와 남은 작업

- S3/MinIO/Ceph, OpenAI 호환 AI, PySpark, 내부 SQL·API·로컬 파일 기능은 유지했다. 실제 사내 서비스 연결과 Spark 연산 검증을 새로 수행한 것은 아니다.
- 실행 중인 컨테이너에서 `pyairtable`을 수동 제거하지 않았다. 의존성 선언 제거까지만 적용했으며 패키지 실물·이미지 크기는 C3 이미지 재빌드에서 확인한다.
- `algoliasearch`는 기존 개발 환경에도 설치되지 않았고 의존성 선언도 없었다.
- 나머지 클라우드 런타임 C2, 전체 SDK 정리 C3, Compute 배포 라우팅은 별도 승인 대상이다. 원본 3100 비교 환경은 변경하지 않았다.
