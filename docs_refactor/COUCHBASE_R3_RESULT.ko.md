# R3b — Couchbase 적용 결과

2026-09-19. [승인된 변경안](COUCHBASE_R3_PLAN.ko.md)에 따라 Python 3.10을 유지하고 Couchbase SDK 로딩 오류를 수정했다. 변경은 로컬 작업 트리에 있으며 커밋·GitHub push·기존 실행 이미지 교체는 하지 않았다.

## 변경 내용

- `mage_integrations/requirements.txt`: Python 버전별 Couchbase 4.1.1/4.3.5 선택을 `couchbase==4.3.5`로 통일했다.
- `Dockerfile`: runtime의 로컬 wheel 설치 명령에 `--only-binary couchbase`를 추가했다. 대상 플랫폼의 Couchbase wheel이 없으면 소스 빌드로 전환하지 않고 실패한다. OS에 구형 OpenSSL 1.1을 추가하지 않았다.
- `tests/sources/couchbase/test_couchbase.py`: 파일 전체가 문자열이라 실행되지 않던 테스트를 활성 테스트 4개로 교체했다.
- `tests/connections/test_couchbase.py`: 단위 테스트 4개와 실제 서버 테스트 5개를 추가했다. 실제 서버 테스트는 `MAGE_TEST_COUCHBASE_URL`이 있을 때 실행된다.
- `connections/couchbase/__init__.py`: 없는 scope가 빈 collection 목록으로 처리되던 동작을 명시적인 오류로 변경했다.
- `sources/couchbase/__init__.py`: 연결 테스트가 bucket 객체 생성에 그치지 않고 실제 scope/collection 조회를 수행하도록 변경했다. 없는 scope가 성공으로 판정되는 문제를 실제 서버에서 발견하여 변경 내용을 먼저 보고한 뒤 보완했다. 연결 테스트 자체가 모든 쿼리 권한을 검증한다는 의미는 아니다.

## 검증 결과

| 검사 | 결과 |
|---|---|
| Python/runtime | Debian 12, Python 3.10.21, Linux x86_64 |
| SDK native extension | Couchbase 4.3.5 import 성공, `ldd` 누락 라이브러리 없음 |
| Couchbase 테스트 | 최종 runtime에 설치된 wheel로 13개 통과, skip 없음 |
| 기존 회귀 | SDK 변경 후보에서 118개 통과 |
| Delta Lake 로컬·S3 설정 회귀 | SDK 변경 후보에서 13개 통과 |
| 상세 source API | 11개에서 Couchbase를 포함한 12개로 복원 |
| 브라우저 | Sources/Destinations 메뉴 확인, 수집된 오류 0개 |
| 최종 runtime 실행 | 서버 API·번들 frontend·loader → transformer → exporter 통과 |
| runtime/dev 후보 빌드 | 모두 성공 |
| 의존성 검사 | 341개 패키지 검사, 기존 충돌 5건 유지 |

이번 실행에서 서로 다른 테스트 총 144개가 통과했다. 기존 회귀 118개와 Delta Lake 13개, UI 검사는 SDK 변경이 반영된 첫 후보에서 수행했다. 이후 없는 scope 처리를 보완한 최종 후보에서는 Couchbase 13개와 runtime 실행 검사를 수행했다. 실제 MinIO 입출력 5개는 이전 [R3a 검증](DELTA_LAKE_R3_RESULT.ko.md)에서 통과했으며 이번에 재실행한 것으로 계산하지 않았다.

실제 서버는 내부 전용 Podman network의 `docker.io/couchbase/server:community-7.6.2`였다. 이미지 digest는 `sha256:c5a5538c91fe0d3228bb2b205bac7d0ca2298c458081238994412440875ba855`이다. 호스트에 서버 포트를 노출하지 않고 임시 bucket `mage_test`의 `_default` scope/collection에 문서 두 개와 primary index를 만들었다. 실제 SQL++ 조회, `INFER`를 통한 source discovery, collection 조회, 잘못된 비밀번호·없는 bucket·없는 scope의 실패를 확인했다. UI/API 검사 컨테이너의 외부 통신 감사 로그는 0건이었다.

## 후보 이미지

- runtime: `localhost/mage-fork:r3-candidate`, ID `cc7abc4b3939378fdf58f8dbb1f36df45ef3416f249096132fae23fab235abcc`
- dev backend: `localhost/mage-fork-dev:r3-candidate`, ID `d16f244c2cedddd192549a08ea24ad9ac07c5f00691223c5716049368f80ab9c`

빌드 명령은 [로컬 빌드 문서](LOCAL_BUILD.ko.md)에 기록했다. 후보에는 이전 R3a Delta Lake 변경도 포함된다. 기존 3000/6789 개발 컨테이너 및 3100 원본 컨테이너의 이미지는 교체하지 않았다. 개발 컨테이너에는 저장소 소스가 mount되어 있으므로 소스 변경은 보일 수 있지만 새 SDK 설치는 후보 이미지에만 반영되어 있다.

## 의존성과 제한

의도적으로 바꾼 버전 제약은 Couchbase 하나다. 다만 현재 설치에 전체 lock이 없어 R2 후보 대비 재빌드 결과에는 `multidict` 6.8.0 → 6.9.0, `fsspec` 2026.7.0 → 2026.9.0, `platformdirs` 4.11.10 → 4.11.11도 포함되었다. 동일한 requirements만으로 설치 결과 전체가 고정되는 구조는 아니다.

`uv pip check`는 최종 후보에서도 실패하며 기존 5건을 보고한다. typing-inspection/typing-extensions 1건, singer-python의 jsonschema·simplejson·backoff 제약 3건, dbt-mysql/dbt-core 1건이다. 사용자 요청대로 이 충돌 수정과 upstream Dockerfile 그대로의 비교 빌드는 보류했다. Couchbase 수정으로 의존성 전체가 정상화됐다고 판단하지 않는다.

Python 3.11 기반 빌드, 다른 CPU 플랫폼, 사내 Couchbase의 서버 버전·TLS·권한 구성은 검증하지 않았다. SDK 4.3.5의 최신성이나 장기 지원을 보장하는 작업도 아니다.

실행 로그는 로컬 임시 경로 `/tmp/mage-couchbase-r3/`의 `build.log`, `dev-build.log`, `server-tests.log`, `regression.log`, `browser.log`, `smoke.log`에 남겼다. 이 경로는 영구 보관을 보장하지 않는다. 검증용 서버·API 컨테이너와 전용 network는 정리했다. API 컨테이너는 SIGTERM 종료 제한 10초를 넘어 Podman이 SIGKILL로 정리했다. 정리 후 기존 개발 UI(3000)와 API(6789)는 HTTP 200 응답을 확인했다.
