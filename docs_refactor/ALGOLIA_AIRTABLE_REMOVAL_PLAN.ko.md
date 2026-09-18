# C2a Algolia·Airtable 제거 변경안 — 승인 후 적용

2026-09-18. 기존 경량화·C1 변경을 로컬 커밋 `b49f9c837`에 저장한 후 작성했다. 커밋 작성자는 `John <john@example.com>`이며 GitHub push는 하지 않았다. 사용자가 이 변경안을 승인하여 구현했다. 결과와 검증 범위는 [C2a 결과](ALGOLIA_AIRTABLE_REMOVAL.ko.md)를 참고한다. 아래는 승인 당시의 변경 범위다. 구현 시 코드·주석·오류 메시지는 영어로 작성한다.

## 제거 대상 전용 파일 12개

- `mage_ai/io/algolia.py`
- `mage_ai/io/airtable.py`
- `mage_ai/data_preparation/templates/data_loaders/algolia.py`
- `mage_ai/data_preparation/templates/data_exporters/algolia.py`
- `mage_ai/data_preparation/templates/data_loaders/airtable.py`
- `mage_integrations/mage_integrations/connections/airtable/__init__.py`
- `mage_integrations/mage_integrations/sources/airtable/__init__.py`
- `mage_integrations/mage_integrations/sources/airtable/templates/config.json`
- `mage_integrations/mage_integrations/sources/airtable/README.md`
- `mage_integrations/mage_integrations/destinations/airtable/__init__.py`
- `mage_integrations/mage_integrations/destinations/airtable/templates/config.json`
- `mage_integrations/mage_integrations/destinations/airtable/Readme.md`

두 서비스는 외부 SaaS 제거 대상이다. Algolia integration 디렉터리나 Airtable 일반 I/O exporter 템플릿은 현재 목록에서 찾지 못했으므로 존재하지 않는 파일을 삭제 대상으로 포함하지 않았다.

## 공통 파일 변경

| 파일 | 제안 변경 |
|---|---|
| `mage_ai/data_preparation/templates/constants.py` | Algolia loader/exporter, Airtable loader 등록 제거. 기존·신형 UI 및 Browse templates에 반영 |
| `mage_ai/data_integrations/sources/constants.py` | Airtable source 등록 제거 |
| `mage_ai/data_integrations/destinations/constants.py` | Airtable destination 등록 제거 |
| `mage_ai/shared/cloud_features.py` | 제거 대상 집합에 `algolia`, `airtable` 추가. 기존 C1 검증을 통해 템플릿·블록·integration·오래된 기본 템플릿 검색 캐시 처리 |
| `mage_ai/io/utils.py` | Airtable 전용 `map_json_to_airtable` 함수 제거. 검색상 호출자는 삭제 예정 Airtable destination 하나이며 다른 공통 함수는 유지 |
| `mage_ai/io/config.py` | Airtable·Algolia 전용 ConfigKey·VerboseConfigKey 및 매핑 제거. 공통 설정 로더 유지 |
| `mage_ai/io/base.py` | 기존 메타데이터 식별을 위한 enum 값 유지. 실행 지원을 의미하지 않으며 정책에서 명시적으로 거절 |
| `mage_ai/data_preparation/templates/repo/io_config.yaml` | 신규 프로젝트용 Algolia·Airtable 예시 설정 제거. 실행 중인 사용자 프로젝트의 설정·자격증명은 수정하지 않음 |
| `requirements.txt` | `pyairtable`의 기본 및 추가 의존성 선언 두 곳 제거 |
| `setup.py` | `airtable` extra와 `all`의 `pyairtable` 선언 제거. 더 이상 지원하지 않는 extra임을 이전 문서에 기록 |
| `mage_ai/tests/data_preparation/test_cloud_connectors_removed.py` | 두 서비스의 카탈로그·템플릿·기존 캐시·직접 요청 차단, S3·내부 DB 보존 검증 확장 |

UI 컴포넌트의 배치나 블록 종류는 변경하지 않는다. 공통 카탈로그를 통해 두 서비스의 기본 선택지만 없앤다. 기존 사용자 작성 블록·custom template은 이름이나 설명에 두 서비스가 등장한다는 이유만으로 삭제하지 않는다.

`mage_ai/frontend/components/v2/Apps/Browser/System/mocks.ts`에도 서비스 이름이 나타나지만 mock 데이터다. 실행 커넥터 등록과 구분하고 이번 변경에서 임의 삭제하지 않는다.

## 패키지 조사 결과와 범위

- 현재 개발 컨테이너: `pyairtable==2.3.3` 설치. 설치 메타데이터에서 직접 의존 선언은 Mage의 기본·선택적 의존성으로 확인했다.
- `algoliasearch`: I/O 모듈이 import하지만 현재 컨테이너에는 미설치이며 requirements/setup에서도 선언을 찾지 못했다. 존재하지 않는 의존성 삭제 작업을 만들지 않는다.
- Airtable integration은 `pyairtable`을 쓰지만 `mage_integrations/requirements.txt`에는 별도 선언이 없다. 삭제 후에도 불필요한 의존성을 새로 추가하지 않는다.
- 승인 시 `pyairtable` 선언까지만 정리한다. 공유 하위 의존성을 연쇄 삭제하거나 실행 중인 컨테이너에서 수동 uninstall하지 않는다. 새 이미지의 실제 패키지 제거·용량 검증은 C3에서 수행한다.

## 기존 프로젝트 동작

- 제거된 커넥터를 새로 선택하거나 직접 요청하면 기존 C1과 같은 영어 오류를 반환한다. 블록 API의 정책 오류는 `error.code=400`으로 처리한다.
- 기존 파이프라인 조회와 커넥터 외 필드 수정은 유지한다. 제거된 커넥터 설정을 다시 지정하거나 실행하는 경우에는 명시적으로 거절한다.
- 사용자 코드에서 삭제된 모듈을 직접 import하면 ImportError가 발생할 수 있다. 사용자 코드를 자동 변환하지 않는다.
- S3/MinIO/Ceph, OpenAI 호환 AI, PySpark, 내부 SQL·API, 로컬 파일 기능은 보존한다.
- 나머지 C2 클라우드 기능, 전체 SDK 정리, Compute 라우팅, 원본 3100 환경은 이번 변경 범위가 아니다.

## 검증 계획

1. 기존 57개 Python 검증과 Algolia·Airtable 추가 검증 수행. 삭제된 import·템플릿 경로·전용 매핑 잔존 확인.
2. 전체 TypeScript 검사 및 Python 구문 검사.
3. 격리 API에서 기본 템플릿·integration source/destination에서 두 서비스가 빠지고, 직접 요청은 저장·연결 전에 차단되는지 확인.
4. 기존·신형 UI 및 Browse templates에서 두 서비스 미노출, Amazon S3·내부 DB 유지 확인.
5. 기존 캐시 및 legacy 파이프라인 조회·일반 수정·실행 오류 검증. 사용자 프로젝트는 테스트용으로 변경하지 않음.
6. requirements/setup 메타데이터에서 `pyairtable` 재도입이 없는지 확인. 전체 이미지 재빌드는 별도 단계임을 결과에 명시.

**승인 요청 범위:** 위 12개 전용 파일 제거, 공통 등록·설정·전용 helper 정리, `pyairtable` 의존성 선언 제거, 오류 처리·검증·결과 문서화. 사용자 승인 후 구현했다.
