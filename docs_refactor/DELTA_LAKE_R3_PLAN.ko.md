# R3a — Delta Lake S3 호환성 수정 변경안 (적용 완료)

2026-09-19. 최초 승인 전 조사 기록이다. 이후 사용자 승인으로 코드 수정을 적용하고 MinIO 컨테이너에서 검증했다. [적용 결과](DELTA_LAKE_R3_RESULT.ko.md)를 참고한다. 패키지 버전·기존 실행 이미지는 변경하지 않았다. 의존성 충돌 5건은 사용자 요청대로 보류한다. upstream Dockerfile 그대로의 빌드 검증도 별도 후속 작업이다.

## 확인한 원인

설치 SDK는 requirements와 동일한 deltalake 0.20.2다. Mage의 Delta Lake writer와 S3 destination은 upstream 기준 `1912c297f`와 현재 fork 사이에 변경이 없다. SDK 버전·사용 API가 어긋나는 기존 코드 문제로 확인했다.

- `delta_lake/writer.py`에서 가져오는 `PyDeltaTableError`, `MAX_SUPPORTED_WRITER_VERSION`, `DeltaTableProtocolError`가 설치 SDK에 없다. 실제 destination import는 첫 번째 이름에서 실패한다.
- writer가 SDK 내부 함수를 직접 호출하고, base.py는 `table._table`을 자체 RawDeltaTable로 바꾼다. 예외 이름만 수정해도 쓰기 경로 전체의 호환성을 보장할 수 없다.
- `DeltaLakeS3.build_table_uri`가 `posixpath.join`에 문자열 여러 개 대신 list 하나를 전달한다. 해당 표현을 독립 실행하면 TypeError가 재현된다.
- Delta Lake S3의 설정 template·Rust storage options·boto3 client에는 명시적인 내부 endpoint 연결 처리가 없다. 기존 Amazon S3 connector의 MinIO/Ceph 설정 지원과 별개 경로다.
- partition overwrite 후 커밋된 Delta log JSON을 직접 고치는 보정 코드가 있다. 공식 writer로 전환할 때 이 동작을 그대로 중복 적용하면 안 된다.
- Delta log가 없을 때 기존 prefix 객체를 삭제하는 사전 처리도 있다. 정상 테이블 생성과 기존 파일 존재를 구분하도록 함께 정리할 필요가 있다.

## 비변경 재현 실험

R2a 후보 이미지에서 공식 `deltalake.write_deltalake`로 임시 로컬 디렉터리에 실제 데이터를 썼다. 최초 생성 → append → predicate 기반 특정 partition overwrite가 성공했다. id 1/2에 3을 append하고 a partition만 4로 교체했을 때 b partition의 2가 보존되어 최종 값은 2/4였다.

이는 SDK 자체의 해당 로컬 쓰기 경로가 동작함을 확인한 것이다. Mage destination 전체 및 MinIO/Ceph 연결이 이미 수정·검증되었다는 뜻은 아니다.

## 제안하는 수정 범위 — 적용 승인 필요

SDK 0.20.2와 다른 패키지 버전은 유지하고 아래 adapter 코드를 수정한다.

| 파일 | 변경 내용 |
|---|---|
| `mage_integrations/mage_integrations/destinations/delta_lake/writer.py` | 오래된 자체 writer 구현을 공식 write_deltalake 호출을 감싸는 얇은 adapter로 교체. overwrite_schema 인자를 현행 schema_mode로 변환하고 기존 입력 계약을 검사 |
| `.../destinations/delta_lake/base.py` | 공개 DeltaTable 및 TableNotFoundError 기반 조회로 전환. RawDeltaTable 치환 제거. partition overwrite 대상과 schema 옵션을 공식 writer에 전달 |
| `.../destinations/delta_lake/raw_delta_table.py` | 사용처 제거 후 삭제 |
| `.../destinations/delta_lake_s3/__init__.py` | URI 생성 수정, endpoint·path style·session token 전달, 공식 partition overwrite 사용 시 사후 log 수정 제거. log 없는 prefix의 자동 객체 삭제를 없애고 기존 객체가 있으면 명확히 실패하도록 변경 |
| `.../destinations/delta_lake_s3/utils.py` | 사후 Delta log 수정 helper 사용처 제거 후 삭제 |
| `.../destinations/delta_lake_s3/templates/config.json` | 기존 Amazon S3 connector와 같은 aws_endpoint/aws_s3_addressing_style/aws_session_token 키 추가. HTTP 허용은 별도 명시 설정으로 제공 |
| `.../destinations/delta_lake_s3/README.md` | 영어로 내부 endpoint 예시·쓰기 모드·설정·동시 쓰기 제한 설명 |
| `mage_integrations/mage_integrations/tests/destinations/test_delta_lake.py` (신규) | 실제 로컬 write/read 회귀 및 에러·schema·partition 검증 |
| `.../tests/destinations/test_delta_lake_s3.py` (신규) | endpoint·token·URI·실패 시 기존 객체 보존 및 S3 호환 저장소 검사 |
| `docs_refactor/INTERNAL_SERVICES.ko.md`, README 및 결과 문서 | Delta Lake S3 설정과 실제 검증 범위 기록 |

필요한 동작 기준:

- append는 기존 데이터를 보존한다. schema mismatch를 조용히 무시하지 않는다.
- partition 없는 overwrite는 전체 교체, partition 있는 overwrite는 입력에 해당하는 partition만 교체하는 기존 코드 의도를 보존한다. 복합 partition·null·따옴표 포함 값은 잘못된 predicate로 다른 partition을 지우지 않도록 검증한다.
- ignore/error, 빈 입력, 명시 schema 및 timestamp 변환 계약을 확인한다. 타입 변환 등 추가 오류가 발견되면 범위를 보고한 뒤 수정한다.
- 존재하지 않는 테이블과 권한/인증/네트워크 오류를 구분한다. 인증 실패를 빈 테이블로 취급해 생성하지 않는다.
- S3 접근에는 boto3와 delta-rs 두 경로가 있으므로 양쪽에 같은 endpoint·자격증명·region·addressing 설정을 전달한다. 한쪽만 설정하고 완료 처리하지 않는다.
- 기존 AWS_S3_ALLOW_UNSAFE_RENAME 설정이 보장하지 않는 다중 writer 동시성까지 이번 수정으로 해결됐다고 주장하지 않는다.

## 적용 후 검증 순서

1. import 성공과 API destination 상세 목록 복원 확인.
2. 실제 로컬 Delta table 생성/읽기/append/overwrite/partition/schema 검사.
3. 로컬 S3 호환 대체 서버에서 endpoint, path style, Delta log·Parquet 쓰기 및 다시 읽기 검증. 사내 실서비스 정보는 필요하지 않다.
4. 기존 S3·AI·Spark 및 pipeline/API/UI 회귀. 공급자 제거 목록은 복원하지 않는다.
5. 격리 후보에서 검증 결과 보고. 기존 개발 이미지 전환은 별도 검토한다.

이번 승인 범위에 Couchbase SDK/libssl 수정, 의존성 충돌 5건 해결, upstream Dockerfile 전체 빌드, dbt 버전 변경은 포함하지 않는다.

## 근거

- [upstream Mage writer](https://github.com/mage-ai/mage-ai/blob/1912c297f3556913c56181a96e8c5253e0883bf0/mage_integrations/mage_integrations/destinations/delta_lake/writer.py)
- [delta-rs Python 0.20.2 writer](https://github.com/delta-io/delta-rs/blob/python-v0.20.2/python/deltalake/writer.py)
- 재현 스크립트: 호스트 `/tmp/mage-r2/delta_probe.py`. 임시 로컬 데이터를 사용하며 실행 시 자동 정리한다.
