# 자동 외부 통신 제거 및 검증

2026-09-18 현재 개발 소스에 적용했다. S3·내부 AI 설정은 [INTERNAL_SERVICES.ko.md](INTERNAL_SERVICES.ko.md), 개발 서버 실행은 [DEV_SETUP.ko.md](DEV_SETUP.ko.md)를 참고한다.

## 변경 사항

- **Mage 사용 통계:** 호스트/플랫폼/프로젝트/블록/실행 정보 수집과 동기·비동기 HTTP 전송 구현을 제거했다. 기존 호출부가 실행 흐름을 유지하도록 `UsageStatisticLogger`의 명시적 메서드만 남겼으며 즉시 `False` 또는 빈 데이터를 반환한다. 생성자도 Project나 DB를 초기화하지 않는다. 통계 거부 이벤트의 강제 전송도 제거했다.
- **설정 호환성:** 기존 `help_improve_mage: true`를 읽거나 저장해도 유효값은 `false`다. 기존 API 필드는 호환성을 위해 남겼지만 활성화할 수 없다. 새 프로젝트 템플릿의 기본값도 `false`다.
- **버전 확인:** ProjectResource와 이전 ApiProjectsHandler 양쪽의 PyPI 조회를 제거했다. API의 `latest_version`은 호환성을 위해 설치 버전을 반환한다. UI는 현재 버전만 표시하며 업데이트 버튼과 외부 변경 이력 링크를 제거했다.
- **브라우저 통계:** Google Analytics 컴포넌트 초기화를 제거했다. 기존 이벤트 호출 함수는 외부 전송 없이 반환한다.
- **외부 모니터링:** CLI 실행·스케줄러·프로세스 큐의 Sentry 초기화/전송과 New Relic 초기화를 제거했다. 이전 환경변수로 활성화되지 않는다. New Relic의 기존 호출부를 위한 초기화 함수는 `(False, None)`을 반환한다. SDK 의존성 제거는 후속 경량화 단계다.
- **AWS 자동 조회:** Secrets Manager 클라이언트를 모듈 import 때 생성하던 동작을 수정했다. 이전에는 일반 서버 시작 중에도 AWS 메타데이터 주소 `169.254.169.254`로 자격증명 조회를 시도했다. 이제 실제 비밀값을 요청할 때만 클라이언트를 만든다. 이후 [클라우드 실행 제거 단계](CLOUD_EXECUTION_REMOVAL.ko.md)에서 Secrets Manager 기능 자체도 삭제했다.
- **UI:** 통계 제공 토글, 헤더의 외부 지원/클라우드 가입/Pro 테마 안내, 탐색 메뉴의 Pro 배포, 블록 메뉴의 Pro AI 링크를 제거했다. 내부 AI의 실제 생성 기능은 유지한다. 이전 사용자 지정 블록 메뉴의 Pro AI 항목도 걸러낸다.
- **정적 자원:** 폰트와 Monaco는 이미 로컬 자원을 사용하고 있었다. 브라우저에서 해당 자원과 편집기가 외부 CDN 없이 로딩되는 것을 확인했다.

문서 링크와 사용자가 직접 지정하는 연결은 일괄 삭제하지 않았다. 클라우드 커넥터/실행기, OAuth, Git 원격 동기화, 사용자 코드와 추가 패키지 설치 경로는 아직 남아 있다. 이 변경은 모든 기능에 대한 네트워크 차단 정책이 아니다.

## 확인한 범위

- 통계·설정·버전·Secrets Manager 초기화 회귀 검사와 Project API 검사 14개 통과.
- 작업 중 내부 AI/S3 검사까지 포함한 23개 검사도 통과했다. 위 14개와 중복되는 검사가 있으므로 합산하지 않는다.
- 전체 UI `tsc --noEmit --incremental false` 통과.
- `--network none` 컨테이너에서 프로젝트 생성, API/번들 HTML 응답, 로드 → 변환 → JSON 저장 통과. 기존 통계 opt-in을 true로 둔 상태에서도 외부 접속 시도 0건.
- 별도 `--internal` Podman 네트워크의 임시 백엔드/프런트엔드에서 로그인, 프로젝트 설정, 개요, 파이프라인 목록, 편집기 5개 화면을 Chromium으로 확인했다. 모든 화면 HTTP 200, Monaco 표시, 브라우저 외부 요청 0건, 실패 HTTP 응답 0건, page error 0건.
- 같은 임시 백엔드의 Python 외부 접속 감시 기록 0건. 이 서버에는 테스트용 Sentry DSN과 `ENABLE_NEW_RELIC=True`도 지정했다.
- 감시 코드가 임의 외부 호스트 조회를 실제로 차단하고 기록하는 자체 검사도 통과했다.

실제 사내 MinIO/Ceph 및 AI 연결은 접속 정보가 없어 아직 검증하지 않았다. 기본 파이프라인 이외의 모든 커넥터와 예약 실행 시나리오를 검증한 것은 아니다. 브라우저 검사는 새 개발 UI를 대상으로 하며, 기존 배포용 번들 HTML 응답 검사는 화면 기능 검증과 구분한다.

## 재현

아래 Python 검사는 현재 개발 이미지와 소스 마운트를 사용한다.

```bash
podman run --rm --network none -v "$PWD:/workspace:ro" -w /tmp \
  -e ENV=test localhost/mage-fork-dev:backend python -m unittest \
  mage_ai.tests.usage_statistics.test_disabled \
  mage_ai.tests.api.endpoints.test_projects
```

네트워크 감시를 포함한 기본 스모크 검사:

```bash
podman run --rm --network none -v "$PWD:/workspace:ro" \
  -e MAGE_OFFLINE_AUDIT=1 \
  -e MAGE_OFFLINE_AUDIT_LOG=/tmp/outbound.jsonl \
  -e PYTHONPATH=/workspace/scripts/offline_network_guard:/workspace:/workspace/mage_integrations \
  localhost/mage-fork-dev:backend sh -c '
    python /workspace/scripts/smoke_test_local_build.py --source-root /workspace &&
    if test -s /tmp/outbound.jsonl; then cat /tmp/outbound.jsonl; exit 1; fi
  '
```

`scripts/offline_network_guard/sitecustomize.py`는 테스트에서만 명시적으로 활성화한다. Python의 DNS/소켓 감사 이벤트를 감시해 외부 연결 시도를 기록하고 거부한다. Loopback, 서버 bind 주소, 자기 호스트명과 `.local` 자기 호스트명 조회, Unix socket은 허용한다. 운영 컨테이너에는 이 제한을 걸지 않는다. 내부 S3/AI를 차단하지 않기 위해서다. 이 감시는 OS 패킷 캡처나 모든 네이티브 라이브러리의 네트워크 감사와 동일하지 않으므로 컨테이너 네트워크 차단을 함께 사용했다.

브라우저 검사는 다음 파일로 재현할 수 있다.

- `scripts/prepare_offline_ui.py`: `/tmp/offline-project`에 테스트 파이프라인을 만들고 서버를 시작한다. 반드시 위 감시 환경변수를 넣은 임시 컨테이너에서 실행한다.
- `scripts/verify_offline_ui.cjs`: 기본 `http://localhost:3001`의 개발 UI를 검사한다. 다른 주소는 `MAGE_TEST_FRONTEND_URL`로 지정한다. 브라우저 요청은 localhost/127.0.0.1만 허용하고 나머지는 기록 후 거부한다.
- Node에서 Playwright를 사용할 수 있어야 한다. `PLAYWRIGHT_MODULE_PATH`로 패키지 경로를, 필요하면 `PLAYWRIGHT_CHROMIUM_EXECUTABLE`로 설치된 Chromium 실행 파일을 지정한다. 결과는 기본 `/tmp/mage-ui-audit.json`에 저장한다.

검증 시 임시 백엔드는 localhost:6788, 임시 프런트엔드는 localhost:3001로 게시했다. 프런트엔드에는 `NEXT_PUBLIC_DEV_API_PORT=6788`을 지정하고 두 컨테이너 모두 외부 경로가 없는 별도 Podman internal 네트워크를 사용했다. 기존 운영 중인 프로젝트 데이터와 인증 설정은 검증용으로 변경하지 않았다.

이번 단계에서 GitHub push와 배포 이미지 발행은 하지 않았다. 변경은 현재 개발 서버의 소스 마운트로 적용된다. 기존 실행 이미지와 저장소의 배포용 정적 UI 산출물은 아직 이 변경을 포함하지 않으므로 배포 전에 UI 산출물 생성과 이미지 재빌드가 필요하다.
