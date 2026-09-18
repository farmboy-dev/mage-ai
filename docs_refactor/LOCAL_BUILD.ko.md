# 로컬 fork 이미지 빌드와 검증

소스 수정과 UI 개발 서버 실행은 [DEV_SETUP.ko.md](DEV_SETUP.ko.md)의 `dev.Dockerfile` 및 `compose.dev.yml` 구성을 사용한다.

루트 `Dockerfile`은 현재 작업 디렉터리의 `mage-ai`와 `mage-integrations`를 wheel로 빌드해 설치한다. 커밋하지 않은 소스 수정도 포함되며 GitHub에 push할 필요가 없다. 브랜치는 로컬에서 checkout한 것으로 결정된다. 기존 `FEATURE_BRANCH` build argument는 사용하지 않는다.

이 단계는 설치 대상을 공개 배포본에서 로컬 소스로 변경한다. 전체 extras, 외부 의존성 다운로드, 시작 시 프로젝트 requirements 설치는 아직 기존 동작을 유지한다. 폐쇄망 완성본이나 경량화 완료 이미지가 아니다.

두 패키지를 함께 설치할 때 드러난 기존 의존성 불일치도 정리한다. `setup.py`의 Kafka 2.0.2 고정을 현재 requirements와 같은 2.3.0으로 맞추고, integrations의 SQLAlchemy 1.4 전용 ClickHouse dialect 0.2.x를 SQLAlchemy 2.x용 0.3.x로 맞춘다. 메인 패키지는 이미 SQLAlchemy 2.x를 요구한다. ClickHouse의 해당 버전 의존성은 [0.3.2 배포 소스](https://github.com/xzkostyan/clickhouse-sqlalchemy/blob/0.3.2/setup.py)에 명시되어 있다.

## 빌드

저장소 루트에서 실행한다. Podman 환경은 아래 명령의 `docker`를 `podman`으로 바꾸되, build에는 `--format docker`를 추가하여 Dockerfile의 `SHELL` 설정을 보존한다.

```bash
docker build -t mage-fork:local -f Dockerfile .
```

현재 검증 머신은 AVX가 노출되지 않는 QEMU x86_64 CPU다. 이 환경에서는 기본 Polars가 `SIGILL`로 종료되므로 아래 호환 빌드를 사용한다. 버전은 1.30.0으로 유지하고 staged requirements와 wheel 의존성도 `polars-lts-cpu`로 함께 변경한다. 저장소 requirements 파일 자체는 이 옵션으로 변경되지 않는다.

```bash
podman build --format docker --build-arg POLARS_PACKAGE=polars-lts-cpu \
  -t localhost/mage-fork:step1 -f Dockerfile .
```

위 태그로 빌드했다면 아래 실행/검증 명령에서도 이미지 이름을 `localhost/mage-fork:step1`로 지정한다. `POLARS_PACKAGE`는 `polars` 또는 `polars-lts-cpu`만 허용한다. 일반 CPU용 기본 이미지와 CPU 호환 이미지를 구분해서 관리한다.

패키지 생성까지만 확인하려면:

```bash
docker build --target source-wheels -t mage-fork-wheels:local -f Dockerfile .
```

`source-wheels` stage에 생성된 wheel은 `/wheels/`에 있다. 실행 stage는 이 wheel을 설치하고 설치용 파일을 제거한다. 저장소나 `.git`을 실행 컨테이너에 마운트할 필요가 없다.

기존 `docker-compose.yml`은 `dev.Dockerfile`을 사용하는 개발용 설정이므로 이번 루트 Dockerfile 검증에는 사용하지 않는다.

## 독립 기동

```bash
docker run --rm --name mage-fork-local \
  -p 127.0.0.1:6789:6789 \
  -v mage-fork-data:/home/src \
  -e USER_CODE_PATH=/home/src/project \
  mage-fork:local
```

브라우저에서 `http://localhost:6789`에 접속한다. 프로젝트와 실행 데이터는 이름 있는 볼륨에 보존된다. 인증 설정은 애플리케이션 기본값을 따른다.

## 패키지·서버·파이프라인 스모크 테스트

```bash
docker run --rm --network none \
  -v "$PWD/scripts/smoke_test_local_build.py:/tmp/mage-smoke.py:ro" \
  mage-fork:local python /tmp/mage-smoke.py
```

테스트는 로컬 wheel 설치 출처, UI/템플릿/DB 설정 파일의 패키지 포함, ClickHouse dialect의 SQLAlchemy 2 SQL 컴파일, 서버 API와 HTML 응답, 세 블록 파이프라인 실행 결과를 확인한다. 임시 프로젝트에서 `[1, 2, 3]`을 `[2, 4, 6]`으로 변환해 JSON 파일에 저장한다. 테스트 인스턴스에만 인증/사용 통계 비활성화를 적용하고 종료 시 임시 데이터와 프로세스를 정리한다. 실제 프로젝트 볼륨은 사용하지 않는다.

이 검증은 브라우저 상호작용, 사내 DB, S3, AI, 예약 실행 전체를 검증하지 않는다. 네트워크가 차단된 테스트 성공도 모든 기능에서 외부 요청 시도가 없다는 보장은 아니다.

프런트엔드는 현재 저장소의 `server/frontend_dist` 및 `frontend_dist_base_path_template`을 패키지에 포함한다. 이후 TSX를 수정할 때는 해당 정적 산출물을 재생성한 뒤 이미지를 빌드해야 한다.

## 2026-09-17 검증 결과

현재 애플리케이션 소스(`1912c297f`)를 기반으로 빌드 경로와 위 의존성 선언을 수정한 결과다. 애플리케이션 기능 제거는 아직 수행하지 않았다. GitHub push와 원격 이미지 publish는 하지 않았다.

- 엔진/플랫폼: rootless Podman, linux/amd64, Python 3.10.21.
- 실행 검증 이미지: `localhost/mage-fork:step1-cpu`, 동일 이미지 별칭 `localhost/mage-fork:step1`.
- 이미지 ID: `39c86b0a607e5e93b855300cd462c4ed8e28c913ead8e6277413cd2d2915b385`.
- 이미지 크기: 4,113,529,712 bytes (약 4.11 GB, Podman 로컬 이미지 Size). 후속 경량화의 기준값이며 압축 전송 크기나 변경 전후 절감량은 아니다.
- 일반 Polars 이미지도 `localhost/mage-fork:step1-standard`로 빌드했으나 이 CPU에서는 `mage init`이 SIGILL로 종료된다. 현재 머신은 CPU 호환 태그를 사용해야 한다.

| 검사 | 결과 |
|---|---|
| 두 로컬 wheel 빌드·설치 | 통과. `direct_url.json`으로 로컬 wheel 출처 확인 |
| 실제 설치 파일과 checkout 비교 | 3,978개 파일 일치. 두 패키지의 LICENSE 포함/내용 일치 |
| CPU 호환 wheel 의존성 | `polars-lts-cpu==1.30.0` 확인 |
| ClickHouse SQLAlchemy 2 dialect | 외부 DB 연결 없이 DDL 컴파일 통과 |
| 임시 프로젝트 생성 | 통과 |
| 서버 API·번들 HTML | 네트워크 차단 컨테이너에서 통과 |
| 로드 → 변환 → 저장 | `[1,2,3]` → `[2,4,6]` JSON 저장 확인 |
| 이미지 기본 CMD | 별도 네트워크 차단 컨테이너에서 HTML 응답 확인 |
| 설치 패키지 전체 정합성 (`pip check`) | 아래 기존 의존성 불일치 5건 남음 |
| 문법/공백 검사 | 스모크 스크립트 Python 문법, `git diff --check` 통과 |

기본 실행 검증은 성공했지만, Dockerfile이 개별 설치하는 기존 패키지까지 전체 의존성이 정합한 상태는 아니다. 별도 Git 패키지 설치 후 메인 requirements를 설치하는 기존 구조에서 다음 문제가 남는다:

```text
typing-inspection 0.4.4 -> typing-extensions>=4.15.0 필요, 설치값 4.11.0
singer-python 5.13.0 -> backoff==1.8.0 필요, 설치값 2.2.1
singer-python 5.13.0 -> jsonschema==4.17.0 필요, 설치값 4.26.0
singer-python 5.13.0 -> simplejson==3.11.1 필요, 설치값 4.1.2
dbt-mysql 1.7.0a1 -> dbt-core~=1.8.0 필요, 설치값 1.10.20
```

이번 단계에서는 해당 연동을 임의로 삭제하거나 버전 제약을 무시하는 패치를 하지 않았다. 후속 커넥터/의존성 정리에서 보존할 기능에 맞춰 제거·교체·격리해야 한다. 전체 커넥터의 운영 가능 판정에는 별도 검증이 필요하다.

기본 CMD 컨테이너 정리 시 SIGTERM만으로 10초 내 종료되지 않아 Podman이 SIGKILL로 정리한 동작도 관찰했다. 기존 entrypoint와 서버/자식 프로세스 종료 처리는 후속 시작 스크립트 정리 시 확인할 항목이다. 테스트용 컨테이너는 제거했으며 기존 컨테이너/볼륨은 변경하지 않았다.

## R2 후보 이미지 검증

R2 경량화 이미지는 기존 태그를 덮어쓰지 않고 빌드한다. 현재 실행 컨테이너에서 패키지를 수동 제거하지 않는다.

```bash
podman build --format docker --build-arg POLARS_PACKAGE=polars-lts-cpu \
  -t localhost/mage-fork:r2-candidate -f Dockerfile .
podman build --format docker --target backend \
  --build-arg MAGE_RUNTIME_IMAGE=localhost/mage-fork:r2-candidate \
  -t localhost/mage-fork-dev:r2-candidate -f dev.Dockerfile .
```

`dev.Dockerfile`은 runtime의 의존성을 상속하므로 두 단계를 모두 빌드한다. 설치 목록·wheel metadata·`pip check`·실행 검증 결과는 [R2 적용 결과](DEPENDENCIES_R2_RESULT.ko.md)에 기록한다. 빌드 성공만으로 기존 의존성 충돌이나 Spark 실서비스 연결이 해결됐다고 판단하지 않는다.
