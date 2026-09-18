# 로컬 개발 환경

자동 외부 통신 제거 결과와 검증 절차는 [OFFLINE_RUNTIME.ko.md](OFFLINE_RUNTIME.ko.md)에 정리했다.

내부 S3·AI 연결 설정은 [INTERNAL_SERVICES.ko.md](INTERNAL_SERVICES.ko.md)를 참고한다.

`dev.Dockerfile`과 `compose.dev.yml`로 백엔드와 Next.js 개발 서버를 실행한다. Python 의존성은 루트 Dockerfile로 만든 실행 이미지에서 그대로 가져오고, 백엔드·integrations·UI 소스를 마운트해 수정 사항을 반영한다. GitHub push나 이미지 배포는 필요 없다.

## 현재 머신에서 실행

이미 빌드된 `localhost/mage-fork:dev-base`, `localhost/mage-fork-dev:backend`, `localhost/mage-fork-dev:frontend`를 사용한다.

```bash
cd /home/jw/mage-ai
podman-compose -f compose.dev.yml up -d
podman-compose -f compose.dev.yml logs -f server app
```

- 개발 UI: http://172.16.0.134:3000/sign-in (현재 LAN 주소)
- 로컬 UI: http://localhost:3000/sign-in
- 백엔드: http://localhost:6789/api/statuses
- 중지: `podman-compose -f compose.dev.yml stop`
- 컨테이너 제거: `podman-compose -f compose.dev.yml down` (데이터 볼륨 유지)

두 포트는 localhost와 현재 사내망 IP `172.16.0.134`에만 바인딩된다. 서버 IP가 바뀌면 `compose.dev.yml`의 포트 바인딩도 수정해야 한다. 개발 UI는 `NEXT_PUBLIC_DEV_API_PORT=6789` 설정으로 브라우저에서 접속한 호스트의 백엔드를 사용한다. API, WebSocket, 이벤트 스트림에 같은 규칙을 적용하며, 프로덕션 빌드의 주소 선택은 유지한다. 사내망에서는 서버 IP로 접속한다. Tailscale 인터페이스에는 포트를 바인딩하지 않는다. 접근 네트워크에서 3000과 6789 포트에 모두 도달할 수 있어야 한다. 인증은 계속 활성화한다.

이 환경에는 `podman-compose` 1.6.0을 `/home/jw/.local/share/mage-dev-tools`에 격리 설치하고 `/home/jw/.local/bin/podman-compose`로 연결했다. 다른 머신에서는 Docker Compose 또는 Podman Compose를 별도로 준비한다.

## 처음부터 빌드

현재 검증 머신은 AVX가 없는 CPU이므로 호환 Polars 패키지를 선택한다. 일반 CPU에서는 `POLARS_PACKAGE` 인자를 생략할 수 있다.

```bash
podman build --format docker \
  --build-arg POLARS_PACKAGE=polars-lts-cpu \
  -t localhost/mage-fork:dev-base -f Dockerfile .
podman-compose -f compose.dev.yml build
podman-compose -f compose.dev.yml up -d
```

검증된 기존 이미지를 재사용하려면 첫 번째 빌드 대신 다음 명령으로 태그를 붙인다.

```bash
podman tag localhost/mage-fork:step1-cpu localhost/mage-fork:dev-base
```

Docker에서는 `podman build --format docker`를 `docker build`로, `podman-compose`를 `docker compose`로 바꾼다. 실제 실행 검증은 Podman에서 수행했다. 다른 실행 이미지를 쓸 때는 `MAGE_RUNTIME_IMAGE=<로컬 이미지 태그> podman-compose -f compose.dev.yml build server`로 지정한다.

이 개발 환경은 새 `compose.dev.yml`을 기준으로 한다. 기존 `docker-compose.yml`은 이전 `/home/src` 마운트와 실행 방식을 사용하므로 이 설정과 혼용하지 않는다.

## 변경 반영과 데이터

| 변경 대상 | 반영 방법 |
|---|---|
| `mage_ai` Python 코드 | `/workspace`에서 직접 import. 서버가 감시하는 Python 모듈은 Tornado가 자동 재시작 |
| `mage_integrations` Python 코드 | `/workspace/mage_integrations`에서 직접 import. 이미 로드된 작업 프로세스는 작업 재실행 또는 서버 재시작 필요 |
| 프런트엔드 TSX | Next 개발 서버의 Fast Refresh |
| Python 의존성 | 기본 실행 이미지와 개발 백엔드 이미지를 다시 빌드하고 컨테이너 재생성 |
| `package.json`/`yarn.lock` 의존성 | 프런트엔드 이미지를 다시 빌드하고 컨테이너 재생성 |

필요하면 `podman-compose -f compose.dev.yml restart server`로 서버를 재시작한다. 이미지 변경 후에는 `podman-compose -f compose.dev.yml up -d --force-recreate`를 실행한다.

프런트엔드는 이미지 빌드 시 고정된 yarn.lock으로 설치하고 캐시를 보관한다. 시작 스크립트는 이 캐시에서 `yarn install --offline --frozen-lockfile`로 의존성 볼륨을 갱신한다. 새로운 의존성을 추가하고 이미지를 재빌드하지 않으면 캐시 부족으로 시작이 실패할 수 있다. Next는 프로젝트에 설치된 버전을 사용하며 사용 통계 전송을 비활성화했다.

`dev_data` 볼륨은 `/var/lib/mage`에 연결된다. 프로젝트는 `project`, 실행 데이터는 `data`, SQLite DB는 `orchestration.db`에 저장된다. `frontend_modules`와 `frontend_next`는 각각 node_modules와 Next 빌드 캐시다. `down -v`는 프로젝트와 DB를 포함한 이 볼륨들을 삭제하므로 데이터 보존 시 사용하지 않는다.

인증은 기본 활성화다. 이 개발 서버는 루트 이미지의 기존 entrypoint 대신 Python 서버를 직접 실행하므로 프로젝트 requirements를 시작 시 자동 설치하지 않는다. 프로젝트에 필요한 추가 의존성은 이미지에 명시적으로 포함한다.

## 2026-09-17 검증

- 백엔드·프런트엔드 이미지 빌드 및 두 서비스 기동 성공.
- 실행 이미지와 개발 백엔드의 Python 패키지 이름/버전 426개 일치.
- 네트워크 차단된 별도 개발 컨테이너에서 소스 import, 프로젝트 생성, API/번들 HTML, 로드 → 변환 → JSON 저장 스모크 테스트 통과.
- Chromium에서 로그인 화면 표시, 백엔드 API 응답 200, TSX 변경의 Fast Refresh 및 원상 복구 확인. 해당 브라우저 검사에서 page error 없음.
- Python 상수 임시 변경 후 API 응답 변화로 자동 재시작 확인. integrations 소스 수정도 새 Python 프로세스에서 즉시 반영됨. 검증용 변경은 모두 복구.

스모크 테스트 재실행:

```bash
podman run --rm --network none -v "$PWD:/workspace:ro" \
  localhost/mage-fork-dev:backend \
  python /workspace/scripts/smoke_test_local_build.py --source-root /workspace
```

이 단계는 개발 환경 구축이다. 빌드에는 외부 패키지 다운로드가 필요하며 클라우드 기능과 사용자가 설정하는 외부 연동은 아직 남아 있다. 자동 외부 통신의 제거 범위는 OFFLINE_RUNTIME.ko.md를 참고한다. S3/내부 AI의 후속 구현 및 검증 결과는 INTERNAL_SERVICES.ko.md에 기록했다. 실제 사내 서비스와 전체 UI 작업 흐름 검증은 별도다. 기존 의존성 불일치 5건과 기본 이미지 검증 한계는 [LOCAL_BUILD.ko.md](LOCAL_BUILD.ko.md)에 기록했다.
