# R3b — Couchbase 로딩 오류 조사 및 변경안

2026-09-19. 아래는 적용 전 조사와 제안 기록이다. 사용자 승인 후 적용 및 후보 이미지 검증을 완료했다. 최종 변경과 검증 범위는 [적용 결과](COUCHBASE_R3_RESULT.ko.md)를 참고한다.

## 원인

현재 기반 이미지는 Debian 12 Bookworm/Python 3.10이다. `mage_integrations/requirements.txt`가 Python <3.11에는 couchbase 4.1.1, >=3.11에는 4.3.5를 선택한다. 이는 upstream 기본 브랜치 기준 `1912c297f`와 동일하다.

설치된 4.1.1의 couchbase/pycbc_core.so에 ldd를 실행한 결과:

```text
libssl.so.1.1 => not found
libcrypto.so.1.1 => not found
```

따라서 서버 연결 전에 native extension 로딩부터 실패한다. 인증정보나 Couchbase 서버 주소로 해결할 문제가 아니다.

공식 릴리스 노트에 따르면 4.1.9부터 배포 wheel은 BoringSSL을 정적으로 링크하여 별도 OpenSSL 라이브러리를 요구하지 않는다. 소스 빌드는 다른 조건이므로 wheel 설치 여부를 검증해야 한다.

## 후보 실험

R2a runtime 이미지의 임시 컨테이너에서 다음 설치만 수행했다.

```bash
uv pip install --target /tmp/cb --no-deps --only-binary=:all: couchbase==4.3.5
```

PYTHONPATH 앞에 /tmp/cb를 넣고 현재 checkout의 Mage 코드를 읽었다. 결과:

- SDK 4.3.5 확인.
- Mage Couchbase source와 connection 모듈 import 성공.
- 새 pycbc_core.so의 ldd에서 누락 라이브러리 없음. libssl.so.1.1/libcrypto.so.1.1 동적 의존성 없음.
- 시스템 OpenSSL 패키지 추가·기존 SDK uninstall 없이 재현.
- 실제 Couchbase 서버 연결·query·discover는 아직 미검증.

기존 `tests/sources/couchbase/test_couchbase.py`는 파일 전체가 삼중따옴표 문자열로 감싸져 있다. AST 검사상 활성 test class가 없고 unittest가 발견한 테스트 수는 0이다. 기존 회귀 테스트가 Couchbase 동작까지 검증했다고 판단할 수 없다.

## 제안

**Python 3.10에서도 이미 upstream이 다른 Python 버전에 사용하는 4.3.5 wheel을 사용한다.** OS에 과거 libssl1.1을 추가하거나 소스 빌드를 위한 별도 시스템 의존성을 늘리는 안보다 이번 로딩 오류의 수정 범위가 작다. 최신 SDK 전체 업그레이드 제안은 아니며, 4.3.5의 장기 지원 여부를 보장하는 주장도 아니다.

| 수정 파일 | 제안 내용 |
|---|---|
| `mage_integrations/requirements.txt` | Python별 두 줄을 `couchbase==4.3.5`로 통일. 현재 fork의 지원 Python 범위와 wheel 제공 여부 확인 |
| `Dockerfile` | wheel 설치 단계에서 Couchbase만 binary wheel 사용을 강제하는 옵션 추가. 해당 플랫폼 wheel이 없으면 소스 빌드로 조용히 전환하지 않고 실패 |
| `mage_integrations/mage_integrations/tests/sources/couchbase/test_couchbase.py` | 비활성 문자열 테스트를 실제 실행되는 테스트로 교체. infer/combine discovery·문서 변환·쿼리 조립을 검증 |
| `mage_integrations/mage_integrations/tests/connections/test_couchbase.py` (신규 후보) | auth/cluster/bucket/scope/query 호출 계약, 예외 전달 및 실제 SDK import 검사 |
| `docs_refactor/LOCAL_BUILD.ko.md`, README 및 결과 문서 | SDK·wheel·OS 조건, 검증 결과, 제한 기록 |

현재 connection 모듈은 PasswordAuthenticator/Cluster/ClusterOptions와 bucket/scope/query API를 사용한다. 이번 import 실험에서는 코드 수정이 필요하지 않았다. 실제 검증에서 readiness·자원 정리·인증 확인 등 수정이 필요하면 해당 connection/source 파일의 변경 내용을 먼저 보고한다. 특히 기존 test_connection은 bucket 객체를 얻는 호출이므로, 그것만으로 실제 query 성공을 주장하지 않는다.

## 적용 후 검증

1. requirements 및 빌드 wheel metadata의 Couchbase 버전 확인.
2. 별도 후보 runtime/dev 이미지 빌드, ldd 누락 없음·Mage import·integration_sources 상세 API 복원 확인.
3. 활성화한 Couchbase 테스트 및 기존 S3/Delta Lake/AI/Spark 회귀.
4. 필요 시 격리된 로컬 Couchbase 서버 컨테이너를 사용해 bucket/scope/collection 조회, 문서 읽기, SQL++ query 및 discover를 검사. 서버 이미지·버전·서비스 기능을 확정해 기록한다. INFER 지원 여부를 확인하고 미지원 환경에서 mock 통과를 실제 discover 통과로 보고하지 않는다.
5. 잘못된 인증정보·없는 bucket/scope의 실패를 검사하고, 성공하는 객체 생성만으로 연결 검증을 대신하지 않는다.
6. uv pip check를 기존 결과와 비교하여 새 충돌이 없는지 확인한다. 기존 5건을 해결하는 작업은 보류 상태를 유지한다.

기존 3000/6789 및 3100 이미지는 교체하지 않는다. 사내 Couchbase 서버 버전과 연결정보가 없어 특정 사내 환경 호환성까지 확정할 수 없다. upstream Dockerfile 그대로의 빌드 검증은 별도 보류 작업이다.

## 근거

- [공식 SDK 릴리스 노트 — 4.1.9의 SSL wheel 변경 포함](https://docs.couchbase.com/python-sdk/current/project-docs/sdk-release-notes.html)
- [공식 Python·OS 호환성 문서](https://docs.couchbase.com/python-sdk/current/project-docs/compatibility.html)
- [upstream requirements](https://github.com/mage-ai/mage-ai/blob/1912c297f3556913c56181a96e8c5253e0883bf0/mage_integrations/requirements.txt)
- 임시 실험 로그: `/tmp/mage-couchbase-audit/sdk435.log`.

**승인 및 적용 완료.** 실제 검증에서 발견한 없는 scope의 성공 오판도 변경 내용을 먼저 보고한 후 수정했다. 기존 실행 이미지 교체 및 Python 버전 전환은 수행하지 않았다.
