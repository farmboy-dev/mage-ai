# Upstream 기본 브랜치 기준 의존성 재검토

2026-09-19. 사용자 정정에 따라 앞으로 비교 기준은 0.9.79 배포 이미지가 아닌 upstream 기본 브랜치다. 원본 이미지 비교 문서는 역사적 참고 자료로만 유지한다. 이번 검토에서 코드·의존성·이미지는 변경하지 않았다.

## 기준 및 포함 여부

`git ls-remote --symref origin HEAD`에서 실제 기본 브랜치는 `master`, HEAD는 `1912c297f3556913c56181a96e8c5253e0883bf0`으로 확인했다. 사용자가 말한 main은 이 기본 개발 브랜치를 의미하는 것으로 해석한다. 확인 시점에는 refs/heads/main이 반환되지 않았다.

현재 fork와 upstream의 merge-base도 `1912c297f`다. 아래 두 변경은 모두 이 기준 커밋의 조상이므로 이미 fork에 포함되어 있다. 추가 cherry-pick이나 dbt 재업그레이드는 필요하지 않다.

| upstream 변경 | 실제 내용 | fork 상태 |
|---|---|---|
| `3e0c6504a` | Docker 및 CI의 설치를 uv pip install로 전환 | 포함; R2a 후보도 uv로 설치 |
| `009c3bbf4` | dbt-core 1.10.20 및 adapter 갱신, Python >=3.10, 공통 의존성·dbt CLI 호환 처리 | 포함; 보존 adapter 버전 유지 |

## uv의 적용 범위

upstream은 requirements.txt/setup.py를 유지한 채 설치 명령을 `uv pip install`로 바꾸었다. uv.lock은 없고 기존 pyproject.toml은 setuptools 빌드 및 개발 도구 설정을 유지한다. uv sync 기반 프로젝트로 전환하거나 전체 runtime 의존성을 하나의 lockfile로 고정한 변경은 아니다.

현재 fork도 같은 uv 설치 방식을 유지한다. 주된 사내 변경은 로컬 checkout에서 wheel을 만들어 설치하는 구조, dev runtime 상속, CPU 호환 Polars 선택 및 승인된 cloud SDK 제거다. 이전 원본 비교 문서에서 uv 사용을 사내 고유 변경처럼 묶어 표현한 부분은 정정한다. uv 전환 자체는 upstream에서 상속한 것이다.

upstream Dockerfile은 여러 Git 패키지를 차례로 설치한 다음 Mage를 설치한다. CI도 Singer를 먼저 설치하고 requirements를 나중에 설치한다. 따라서 설치가 성공하더라도 앞서 설치한 패키지의 요구 조건과 최종 환경이 어긋날 수 있다. uv 사용만으로 상충하는 버전 조건이 동시에 만족되는 것은 아니다.

## dbt 1.10과 Singer

upstream dbt 변경은 CI에서 Singer 설치를 requirements보다 앞으로 옮겼다. 커밋 설명에도 뒤의 requirements 설치로 dbt 호환 공통 패키지를 복구하는 목적을 명시한다. Singer의 오래된 정확 버전 요구 자체를 고친 변경은 아니다.

현재 선택은 upstream과 같은 dbt-core 1.10.20을 유지하는 것이다. 원본 이미지의 1.8.7로 복원하는 제안은 진행하지 않는다. dbt-mysql fork는 여전히 dbt-core ~=1.8.0을 요구하므로 이 adapter의 호환성 문제는 별도 검증이 필요하다.

## uv 자체 검사 결과

R2a 후보 `localhost/mage-fork:r2-candidate`에서 `uv pip check`를 실행했다. 341개 패키지 검사 후 기존 pip check와 같은 5건이 나왔다.

- typing-inspection → typing-extensions >=4.15.0 요구, 설치 4.11.0.
- singer-python → jsonschema ==4.17.0 요구, 설치 4.26.0.
- singer-python → simplejson ==3.11.1 요구, 설치 4.1.2.
- singer-python → backoff ==1.8.0 요구, 설치 2.2.1.
- dbt-mysql → dbt-core ~=1.8.0 요구, 설치 1.10.20.

이는 현재 후보 이미지의 실제 검사 결과다. upstream 기본 브랜치 전체를 새로 빌드한 결과라고 표현하지 않는다. upstream 선언·설치 순서와 그로부터 상속한 충돌 조건을 확인한 것이다.

## 이후 작업 방향

1. upstream의 uv 설치 방식과 dbt 1.10 버전을 유지한다.
2. typing-extensions는 upstream과 같은 4.11.0을 우선 유지한다. 현재 필수 소비자가 없는 typing-inspection의 잔여 설치 정리와 빌드 순서를 먼저 격리 검증한다. 기본 브랜치 비교로 바꾸어도 이 원인 분석은 유효하다.
3. Singer는 upstream의 순차 설치 방식을 이해한 상태에서 실제 호환성 검증과 선언 정리의 필요성을 판단한다. 기존 패치 초안을 자동 재승인된 것으로 처리하지 않는다.
4. dbt-mysql은 dbt-core 전체 downgrade 없이 1.10 호환성 확보 방안을 조사한다. SQL Server·ClickHouse 등 다른 내부 adapter를 보존한다.
5. uv pip check를 후속 검증 기준으로 사용한다. 전체 요구 조건을 일괄 resolve하고 lock/sync하는 구조는 충돌 해결 후 별도 변경안으로 다룬다. 서로 겹치지 않는 요구 조건은 lockfile 생성만으로 해결되지 않는다.

## 근거

- [uv 설치 전환 commit](https://github.com/mage-ai/mage-ai/commit/3e0c6504a81badc3cfefeef12e71030ca7d1b405)
- [dbt 1.10 변경 commit](https://github.com/mage-ai/mage-ai/commit/009c3bbf420832e8d205d8086c201abd7668393f)
- [확인한 upstream requirements](https://github.com/mage-ai/mage-ai/blob/1912c297f3556913c56181a96e8c5253e0883bf0/requirements.txt)
- [확인한 upstream Dockerfile](https://github.com/mage-ai/mage-ai/blob/1912c297f3556913c56181a96e8c5253e0883bf0/Dockerfile)
- [uv의 환경 locking 문서](https://docs.astral.sh/uv/pip/compile/)
