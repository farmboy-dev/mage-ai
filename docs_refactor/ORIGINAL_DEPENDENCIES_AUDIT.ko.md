# Mage 원본 기준 의존성 재검토

> 후속 사용자 정정: 현재 비교 기준은 [upstream 기본 브랜치](UPSTREAM_MAIN_DEPENDENCIES_REVIEW.ko.md)다. 이 문서의 0.9.79 이미지 비교는 참고 자료이며 rollback 기준이 아니다.

2026-09-19. 사용자 요청으로 0.9.79 원본 기준에서 다시 조사했다. 애플리케이션 코드·의존성 버전·실행 컨테이너는 변경하지 않았다.

## 비교 기준

1. 원본 Git tag `0.9.79`: `6f953279bbe0ac92152cc19d45436b0923c022ff`.
2. 사내 경량화 시작 전 upstream checkout: `1912c297f`. VERSION은 여전히 0.9.79지만 태그 이후 변경을 포함한다.
3. R2a 적용 commit: `ff15b3bf1`, 후보 runtime `daab8b51e344`.
4. 원본 이미지 `docker.io/mageai/mageai:0.9.79`: 별도 임시 컨테이너에서 Python metadata와 pip check만 검사했다. 이미지는 수정하지 않았다.

3100에서 실행 중인 비교 컨테이너에는 CPU 호환용 polars-lts-cpu 교체가 있어 pip check에 polars 누락이 추가로 나온다. 이를 원본 이미지 오류로 오인하지 않도록 변경 없는 새 컨테이너에서 재검사했다.

## 가장 중요한 정정

현재 fork를 원본 0.9.79 태그와 동일한 의존성 기준으로 설명하면 안 된다. dbt 1.10, SQLAlchemy 2, pandas 2 계열 등은 경량화 작업 이전에 upstream에서 바뀐 내용이다. `009c3bbf4`의 upstream dbt 업그레이드가 현재 checkout에 포함되어 있다.

또한 typing-inspection은 현재 설치 환경에서 필수 의존성으로 요구하는 소비자가 없는 잔여 패키지다. R2a 빌드 로그 및 중간 layer에서 dbt-mysql 설치 시 dbt-semantic-interfaces → pydantic 2.13.5 → typing-inspection 0.4.4가 들어왔고, 후속 Mage 설치에서 pydantic이 2.9.2로 바뀌면서 남은 것을 확인했다. 원본 이미지도 pydantic 2.9.2이고 typing-inspection의 필수 소비자가 없지만, 과거 원본 이미지의 상세 설치 순서는 이 조사만으로 단정하지 않는다.

따라서 typing-extensions를 먼저 상향하자는 기존 제안을 철회한다. 원본 pin 4.11.0을 유지하고 잔여 패키지·빌드 순서를 정리하는 방안을 먼저 검증해야 한다. 아직 제거·버전 변경을 적용하지 않았다.

## 원본과 현재의 핵심 버전

| 패키지 | 원본 0.9.79 이미지 설치값 | R2a 후보 설치값 |
|---|---|---|
| typing-extensions | 4.11.0 | 4.11.0 |
| typing-inspection | 0.4.2, extensions >=4.12.0 요구 | 0.4.4, extensions >=4.15.0 요구 |
| pydantic | 2.9.2 | 2.9.2 |
| singer-python | 5.13.0 | 5.13.0 |
| singer-sdk | 0.34.1 | 0.34.1 |
| backoff | 2.2.1 | 2.2.1 |
| jsonschema | 4.26.0 | 4.26.0 |
| simplejson | 3.20.2 | 4.1.2 |
| dbt-core | 1.8.7 | 1.10.20 |
| dbt-mysql | 1.7.0a1 | 1.7.0a1 |
| dbt-sqlserver | 1.8.4 | 1.9.0 |
| dbt-clickhouse | 1.8.5 | 1.10.0 |

## pip check 재현 결과

변경하지 않은 원본 이미지에서도 다음 5건이 나온다.

1. typing-inspection 0.4.2가 typing-extensions >=4.12.0 요구, 설치값 4.11.0.
2. singer-python이 backoff ==1.8.0 요구, 설치값 2.2.1.
3. singer-python이 jsonschema ==4.17.0 요구, 설치값 4.26.0.
4. singer-python이 simplejson ==3.11.1 요구, 설치값 3.20.2.
5. mage-integrations가 kafka-python ~=2.3.0 요구, 설치값 2.0.2.

R2a 후보의 typing 1건과 Singer 3건은 원본에서도 같은 종류의 충돌이 있는 것이다. 세부 설치 버전은 일부 다르다. 원본 Singer Git commit도 `0540a699c0e2fd8ba64c3245b5fa9aa87ae0538c`로 후보와 같다.

원본에는 dbt-mysql 충돌이 없다. dbt-core 1.8.7이 adapter의 ~=1.8.0 요구를 만족한다. 현재 후보의 dbt-mysql 충돌은 태그 이후 upstream에서 dbt-core를 1.10.20으로 올렸으나 같은 MySQL adapter를 유지한 조합에서 발생한다. R2a SDK 삭제가 dbt를 올린 것이 아니다.

원본의 Kafka 충돌은 현재 후보에는 없다. pip check 결과가 두 이미지에서 모두 5건이라고 해서 같은 5건인 것은 아니다.

## 선언 파일 전체 비교

`requirements.txt`, `setup.py` extras, `mage_integrations/requirements.txt`, `Dockerfile`을 세 기준에서 비교했다. [전체 선언 snapshot 및 차이 JSON](ORIGINAL_DEPENDENCIES_AUDIT.json)에 보존한다.

| 비교 | 루트 requirements | integrations requirements |
|---|---|---|
| 원본 태그 → 경량화 시작 전 upstream | 패키지 이름 추가/삭제 없이 33개 선언 변경 | 추가/삭제 없이 7개 선언 변경 |
| upstream 기준 → R2a | 30개 패키지 선언 제거, 1개 변경 | 15개 제거, 1개 변경 |

이 숫자는 파일별 정규화된 패키지 이름 기준이다. 같은 패키지가 여러 파일 또는 여러 조건부 선언에 등장하므로 두 파일의 개수를 합산해 고유 제거 수라고 해석하지 않는다.

사내 작업에서 보존 패키지의 버전 조건을 직접 바꾼 항목은 위 requirements 비교 기준으로 `clickhouse_sqlalchemy`의 `~=0.3.2` 지정이다. 기존 로컬 빌드의 SQLAlchemy 2 호환 조치다. Dockerfile의 소스 wheel 빌드, Polars CPU 호환 선택 및 cloud SDK 제거는 별도의 사내 변경이다. uv 설치 전환 자체는 upstream에서 상속했다. 버전 미고정 의존성은 재빌드 시점에 따라 설치값이 달라질 수 있다.

원본 Dockerfile도 일부 Git HEAD 패키지를 순차 설치한다. 원본 tag의 requirements만으로 과거 배포 이미지의 모든 설치 버전을 재현할 수 있는 lockfile 구조가 아니다.

## 후속 판단

- typing: 원본의 4.11.0 pin 유지, 잔여 typing-inspection 제거/설치 순서 정리 가능성을 격리 검증하는 안으로 변경.
- Singer: 원본부터 있는 충돌이며 실제 동작과 선언 불일치를 구분. 로컬 patch는 선택 사항으로 다시 검토하며 아직 적용하지 않음.
- dbt: 현재 upstream 1.10 유지+MySQL adapter 보완과 원본 1.8 계열 전체 복원은 서로 다른 범위다. MySQL 하나만 보고 dbt-core만 낮추지 않는다. 원본 복원은 다른 adapter·공통 의존성·상위 코드의 회귀가 필요하므로 사용자 요청 없이 진행하지 않음.
- 0.9.79 원본 의존성으로 전부 되돌리는 것은 이번 조사 요청에 포함하지 않는다. 제거한 클라우드 패키지 역시 복원하지 않는다.

## 근거 및 재현

- [0.9.79 requirements.txt](https://github.com/mage-ai/mage-ai/blob/0.9.79/requirements.txt)
- [0.9.79 setup.py](https://github.com/mage-ai/mage-ai/blob/0.9.79/setup.py)
- [0.9.79 Dockerfile](https://github.com/mage-ai/mage-ai/blob/0.9.79/Dockerfile)
- [upstream dbt 1.10 변경](https://github.com/mage-ai/mage-ai/commit/009c3bbf420832e8d205d8086c201abd7668393f)

```bash
podman run --rm --entrypoint python docker.io/mageai/mageai:0.9.79 -m pip check
git diff 0.9.79 1912c297f -- requirements.txt setup.py mage_integrations/requirements.txt Dockerfile
git diff 1912c297f ff15b3bf1 -- requirements.txt setup.py mage_integrations/requirements.txt Dockerfile
```

임시 원본 검사 자료는 `/tmp/mage-original-deps/`에 있다. 실행 중인 원본/개발 컨테이너는 변경하지 않았다.
