# R2b — 의존성 충돌 해결 초안 (원본 재검토로 적용 보류)

> 사용자 요청으로 의존성 충돌 5건 수정은 보류한다. 이후 upstream Dockerfile 기준 빌드에서 재현 여부와 실제 영향을 먼저 확인한다.

> 2026-09-19 정정: [원본 기준 재검토](ORIGINAL_DEPENDENCIES_AUDIT.ko.md)에서 typing-inspection이 잔여 패키지임을 확인했다. 아래 typing-extensions 상향 제안은 철회한다. Singer 충돌은 원본에도 존재하며 dbt 1.10은 태그 이후 upstream 변경이다. 아래 내용은 과거 초안 기록이며, 새 승인 요청으로 사용하지 않는다.

> 현재 후속 기준: [upstream 기본 브랜치 재검토](UPSTREAM_MAIN_DEPENDENCIES_REVIEW.ko.md). uv 설치·dbt 1.10을 유지하며 typing 잔여 패키지부터 검토한다.

2026-09-18. R2a는 `ff15b3bf1`로 로컬 커밋했다. GitHub push 및 실행 이미지 교체는 하지 않았다. 이번 단계는 조사와 변경안 작성이며, 아래 패키지·빌드 코드는 아직 수정하지 않았다.

## 원인

현재 Dockerfile은 Git 패키지를 각각 설치한 뒤 Mage wheel을 별도로 설치한다. 뒤의 설치에서 공통 라이브러리가 교체되어 앞서 설치한 패키지의 요구 조건과 어긋날 수 있다. 현재 R2a 후보 이미지의 설치 metadata를 검사한 결과다.

| 충돌 | 양쪽 요구 | 판단 |
|---|---|---|
| typing-extensions | Mage ==4.11.0 / typing-inspection >=4.15.0 | Mage pin 상향으로 해결 가능 후보 |
| backoff | Singer ==1.8.0 / singer-sdk >=2.0.0 | 양쪽을 만족하는 버전 없음 |
| jsonschema | Singer ==4.17.0 / dbt-core >=4.19.1,<5; Jupyter >=4.18 | 양쪽을 만족하는 버전 없음 |
| simplejson | Singer ==3.11.1 / singer-sdk >=3.17.6 | 양쪽을 만족하는 버전 없음 |
| dbt-core | dbt-mysql ~=1.8.0 / dbt-sqlserver >=1.9,<2; dbt-clickhouse >=1.9 | 공통 dbt downgrade로 해결 불가 |

Singer와 singer-sdk는 서로 다른 패키지이며 현재 둘 다 사용한다. Singer의 catalog/schema/message/state 처리와 singer-sdk 기반 destination을 보존해야 한다. 상위 Singer 저장소의 현재 setup.py도 jsonschema 2.x를 요구하므로, 최신 upstream으로 단순 교체하는 안은 채택하지 않는다.

## 권장 순서

먼저 R2b-1에서 typing/Singer 4건을 검증하고, R2b-2에서 dbt-mysql 1건을 별도로 다룬다. 두 단계가 끝나고 `pip check`가 0건이 되어야 의존성 충돌 해결 완료로 판단한다. 패키지 제거 또는 installed METADATA 파일 직접 수정으로 검사 결과만 바꾸지 않는다.

## R2b-1 — 적용 승인 요청

| 파일 | 구체적 변경 |
|---|---|
| `requirements.txt` | typing_extensions pin을 4.11.0에서 4.15.0으로 변경. 후보 이미지의 Python 3.10 및 확인한 필수 요구 범위와 호환되는 버전 |
| `patches/singer-python/compatibility.patch` (신규) | 현재 사용 중인 Mage Singer commit의 setup.py 요구 조건을 검증 대상 backoff==2.2.1, jsonschema==4.26.0, simplejson==4.1.2로 변경. 로컬 버전 식별자 5.13.0+mage.internal.1 부여. 넓은 버전 범위 전체의 호환성을 주장하지 않음 |
| `patches/singer-python/README.md` (신규, 영어) | 원본 URL·commit·patch 이유·적용법·검증 범위·원본 라이선스 참조 기록 |
| `Dockerfile` | Singer Git HEAD 직접 설치 대신 현재 commit `0540a699c0e2fd8ba64c3245b5fa9aa87ae0538c`의 소스를 빌드 단계에서 가져와 patch를 적용하고 로컬 wheel 생성·설치. patch 불일치 시 빌드 실패. 나머지 Git 의존성은 이 단계에서 변경하지 않음 |
| `mage_integrations/mage_integrations/tests/test_singer_compatibility.py` (신규) | Singer schema 참조 해석, JSON 메시지 직렬화·Decimal/날짜/비정상 수치 계약, state/bookmark, 재시도·giveup 동작의 호환성 검사 |
| `docs_refactor/LOCAL_BUILD.ko.md`, README 및 R2b 결과 문서 | 재현 명령·wheel 출처·잔여 충돌·실행 검증 결과 기록 |

현재 후보에 설치된 Singer 실제 코드에서는 jsonschema의 RefResolver, backoff의 on_exception/expo, simplejson의 메시지 직렬화를 사용한다. R2a의 기본 테스트 통과만으로 모든 호환성이 입증된 것은 아니다. 위 경계 동작과 기존 source/destination 회귀가 통과해야 patch를 채택한다. 소스 호환성 수정까지 필요하면 추가 파일·변경 내용을 먼저 보고한다.

검증 및 완료 기준:

1. 원본 commit 고정·patch 적용·wheel metadata의 로컬 버전/요구 조건 확인.
2. Singer 호환성 및 보존 source/destination 테스트, 기존 118개 회귀 테스트.
3. 별도 후보 runtime/dev 이미지 빌드. 기존 3000/6789/3100 환경은 교체하지 않음.
4. pip check를 기존 5건과 비교하여 typing/Singer 4건이 사라지고 dbt-mysql 1건만 남는지 확인. 다른 충돌 발생 시 완료 처리하지 않음.
5. S3·OpenAI 호환·Spark kernel/env·내부 adapter import·로컬 pipeline/API/UI·외부 연결 감사.

## R2b-2 — dbt-mysql, 후속 상세 승인

현재 Mage fork commit `713545c17ca6cbdcf57441a08bb72ebf08827ce2`의 dbt-core 요구는 1.8 계열이다. import 성공만으로 1.10에서의 model 실행·relation 처리·incremental 동작을 보장할 수 없다.

dbt-core 1.10.20 및 다른 내부 adapter를 유지하면서 MySQL adapter의 실제 API 호환성을 조사한다. 호환 release 교체 또는 고정 소스 patch를 비교하되 요구 버전 문자열만 넓혀 끝내지 않는다. 로컬 임시 MySQL 서버에서 연결·seed·table/view·incremental·test를 실행할 수 있는 재현 검증이 필요하다. 실제 사내 DB의 인증정보는 필요하지 않다.

adapter 변경 파일과 검증용 DB 이미지/버전을 확정한 별도 변경안을 제시한 후 적용한다. 모든 충돌 해소 뒤에는 관련 wheel을 함께 resolve하고 빌드 마지막에 `pip check`를 실패 조건으로 넣는 방안을 포함한다. 현재 단계에서 그 조건을 넣으면 이미 알려진 dbt-mysql 충돌 때문에 빌드가 실패한다.

## 근거

- [현재 Mage Singer 고정 commit의 setup.py](https://github.com/mage-ai/singer-python/blob/0540a699c0e2fd8ba64c3245b5fa9aa87ae0538c/setup.py)
- [현재 Mage dbt-mysql 고정 commit의 setup.py](https://github.com/mage-ai/dbt-mysql/blob/713545c17ca6cbdcf57441a08bb72ebf08827ce2/setup.py)
- [상위 Singer setup.py](https://github.com/singer-io/singer-python/blob/master/setup.py), 2026-09-18 조회. 이 가변 URL을 빌드 입력으로 쓰지 않음.
- [typing-extensions 4.15.0 배포 정보](https://pypi.org/project/typing-extensions/4.15.0/): Python >=3.9.
- 현재 설치된 패키지의 역방향 필수 의존성: `/tmp/mage-r2/reverse-conflicts.json`. optional extras는 제외하고 현재 환경 marker 기준으로 조사.

**이 초안의 적용 승인 요청은 원본 재검토로 보류했다. 새 변경안을 작성한 뒤 검토받는다.** R2b-2의 MySQL adapter 변경, R3의 Couchbase/Delta Lake 수정 및 개발 이미지 전환은 별도 검토 후 진행한다.
