# Upstream Dockerfile 빌드 비교

2026-09-19. 사용자 요청에 따라 기존 로컬 소스 빌드 파일을 `Dockerfile_refactor`로 보존하고, `Dockerfile`에는 upstream 원본을 복원했다. 개발 환경 및 로컬 빌드 문서의 명령도 새 파일명을 사용한다.

## 기준과 재현

- upstream: `mage-ai/mage-ai`, `master` 커밋 `1912c297f3556913c56181a96e8c5253e0883bf0`
- 원본: https://github.com/mage-ai/mage-ai/blob/1912c297f3556913c56181a96e8c5253e0883bf0/Dockerfile
- 원본과 복원 파일 SHA-256: `ef55ac0ff626f2b83645fbcbd6b49636e7ff6b8ebcd934a634c4ba19f3a2036c`

```bash
podman build --format docker -f Dockerfile \
  -t localhost/mage-fork:upstream-dockerfile-check .
```

원본 파일은 변경 없이 실행한다. `FEATURE_BRANCH`는 지정하지 않았다. 설치하는 Mage 본체는 checkout의 버전 상수에 따른 PyPI `mage-ai[all]==0.9.79`이며 integrations는 upstream Git 저장소에서 설치한다. 로컬 fork의 requirements 변경을 검증하는 빌드가 아니다. 시작 스크립트와 버전 상수는 현재 checkout에서 복사한다.

`FEATURE_BRANCH=refactor`만 지정해도 fork 주소로 전환되지 않는다. 원본 파일에 저장소 주소가 `mage-ai/mage-ai`로 고정되어 있기 때문이다. fork 설치 검증은 저장소 주소 변경 또는 별도의 소스 설치 전략이 필요하다.

## 진행 상태

원본 파일 빌드는 exit 0으로 성공했다. 이미지 ID는 `67754b38b31d81ff8d4e32d14fe8feaca5fb339e1999e8ed53557f548e326b0e`이다. Python 3.10.21, Mage 0.9.79, upstream integrations `1912c297f`, Couchbase 4.1.1, dbt-core 1.8.7이 설치됐다.

`uv pip check`는 413개 패키지를 검사하여 충돌 11건을 보고했다:

| 요구하는 패키지 | 요구 조건 | 설치 버전 |
|---|---|---|
| google-analytics-data | google-api-core[grpc]>=2.28.0,<3.0.0 | 2.15.0 |
| google-analytics-data | protobuf>=6.33.5,<8.0.0 | 4.25.9 |
| typing-inspection | typing-extensions>=4.15.0 | 4.11.0 |
| singer-python | jsonschema==4.17.0 | 4.26.0 |
| singer-python | simplejson==3.11.1 | 4.1.2 |
| singer-python | backoff==1.8.0 | 2.2.1 |
| mage-integrations | google-cloud-bigquery~=3.30.0 | 3.14.1 |
| mage-integrations | kafka-python~=2.3.0 | 2.0.2 |
| mage-integrations | protobuf>=6.0,<7 | 4.25.9 |
| mage-integrations | redshift-connector>=2.1.8 | 2.0.915 |
| mage-integrations | snowflake-connector-python>=4.0.0 | 3.7.1 |

기존 fork의 5건 중 typing 1건과 Singer 3건은 재현됐다. dbt-mysql/dbt-core 충돌은 이번에 없지만 dbt-core가 1.8.7로 내려갔기 때문이며, fork의 1.10 환경 문제가 해결됐다는 의미가 아니다. 나머지 7건은 위 Google 관련 2건과 integrations 요구 조건 5건이다. 이 결과는 기본 빌드의 최신 integrations와 PyPI 0.9.79 본체 조합에 대한 결과다. upstream master의 본체까지 설치한 결과로 해석하면 안 된다.

## 실행 진입 검사

호스트 포트나 repository mount 없이 `--network none` 임시 컨테이너에서 모듈 import를 개별 프로세스로 검사했다.

- `couchbase.cluster`: `libssl.so.1.1` 누락으로 exit 1. 이전 SDK 문제 재현.
- `mage_ai.server.server`: Polars가 AVX 등 CPU 기능 누락을 경고한 뒤 SIGILL(exit -4)로 종료. 현재 호스트에서 이 원본 이미지의 서버 실행을 정상 판정할 수 없다.

따라서 **이미지 빌드는 성공했으나 의존성 검사와 서버 실행 진입 검사는 실패**했다. Polars 교체 등 원본을 바꾸는 수정은 하지 않았다. 기존 개발·원본 실행 컨테이너도 교체하지 않았다.

로그는 `/tmp/mage-upstream-build/`의 `build.log`, `dependency-check.log`, `import-check.log`에 보관한다. 임시 로그는 영구 보관을 보장하지 않는다.

로컬 `refactor` 브랜치의 `4ec7e887e` 커밋에 기존 R3a/R3b 변경과 Dockerfile 분리를 포함했다. 업로드 대상 remote는 `fork` (`https://github.com/farmboy-dev/mage-ai.git`)이며 기존 `origin`은 보존했다. HTTPS push는 인증정보가 없어 실패했다. 토큰 등의 비밀정보는 저장소와 문서에 넣지 않는다.
