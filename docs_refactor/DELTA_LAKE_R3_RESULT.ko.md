# R3a — Delta Lake S3 수정 및 MinIO 검증 결과

2026-09-19. [승인된 변경안](DELTA_LAKE_R3_PLAN.ko.md)을 적용했다. SDK는 deltalake 0.20.2 그대로이며 의존성 선언·Dockerfile을 수정하지 않았다. 이번 코드 변경은 아직 커밋하지 않았다.

## 변경 내용

- 자체 writer의 SDK 내부 API 사용을 없애고 공개 DeltaTable/write_deltalake API를 사용한다. 테이블이 없을 때만 TableNotFoundError를 처리하고 인증·네트워크 오류는 전달한다.
- RawDeltaTable wrapper와 커밋 후 Delta log를 다시 쓰던 helper를 삭제했다. partition overwrite는 SDK의 predicate와 transaction으로 처리한다.
- S3 URI 생성 오류를 수정하고 boto3·delta-rs 양쪽에 내부 endpoint, path/virtual addressing, region, session token을 전달한다. HTTP endpoint는 aws_allow_http=true를 명시해야 한다.
- Delta log가 없는 경로에 파일이 있으면 삭제하지 않고 실패한다. 기존 테이블의 빈 batch overwrite도 데이터를 삭제하지 않는다.
- 구현 중 보고한 base.py 타입 변환을 보완했다. False/null을 보존하고 nullable 숫자 타입을 문자열로 바꾸지 않는다. 큰 정수의 DataFrame 생성 중 정밀도 손실을 방지한다. array는 문자열 원소 목록, object는 JSON 문자열로 처리하며 잘못된 boolean·정수·non-nullable null은 실패한다.
- SDK predicate 처리 문제로 큰따옴표가 포함된 partition 컬럼명은 overwrite 전에 명시적으로 거절한다. 작은따옴표 포함 partition 값, null, 복합 partition의 다른 조합 보존을 검사했다.

## MinIO 환경

사용자 승인에 따라 테스트 전용 MinIO를 실행했다.

- 이미지: `quay.io/minio/minio:RELEASE.2025-04-22T22-12-26Z`
- digest: `sha256:3f97c5651cb6662b880c787a232b6b34fec8d8922e08d6617b25d241a21164bb`
- 네트워크: `podman network create --internal mage-delta-test`
- endpoint: 테스트 네트워크 내부의 `http://minio:9000`. 호스트에 MinIO 포트를 공개하지 않았다.
- 임시 인증정보와 무작위 테스트 bucket만 사용했다. 테스트 cleanup으로 객체·bucket을 정리한다.
- runner: R2a runtime 이미지에 현재 checkout을 읽기 전용 mount했다. SDK 버전 및 기존 의존성은 그대로 사용했다.

## 검증 결과

| 검사 | 결과 |
|---|---|
| Delta 전용 테스트 | 18개 통과; 그중 MinIO 실제 연결 테스트 5개 |
| 로컬 Delta table | 생성·append·ignore·error·전체 overwrite·빈 입력·schema 변경·timestamp·batch reader 검사 |
| partition 교체 | 복합 partition, null, 작은따옴표 값, 다른 partition 보존 및 이전 table version 읽기 확인 |
| MinIO 실제 입출력 | SDK wrapper 및 Mage destination export_batch_data로 쓰기·읽기 성공 |
| 타입 보존 | False/null/2^53 초과 정수, array/object, 잘못된 값 거절 확인 |
| Delta log | overwrite 후 이전 commit 파일의 byte 내용이 그대로인지 확인 |
| 기존 파일 보호 | Delta log 없는 prefix의 keep.txt가 실패 후에도 그대로 존재 |
| 인증 실패 | 잘못된 secret으로 boto3 연결과 DeltaTable 조회 모두 실패; missing table로 처리하지 않음 |
| 기존 기능 회귀 | 별도 118개 테스트 통과: API·S3·AI·Spark·설정·streaming 등 |
| 상세 API | integration_destinations 13개 반환, Delta Lake S3와 새 설정 template 정상 제공; 기존에는 import 오류로 상세 목록에서 누락 |
| 브라우저 | 기존 frontend를 격리 backend로 연결해 Sources/Destinations 검사, 오류 0개 |
| API/UI 외부 연결 감사 | 격리 backend 감사 기록 0건. MinIO 테스트는 외부 라우팅 없는 별도 내부 네트워크 사용 |
| 개발 환경 | 기존 3000/6789 HTTP 200, 개발 및 원본 이미지 교체 없음 |
| 변경 형식 | git diff --check 통과 |

TypeScript 코드는 변경하지 않았다. 기존 runtime 이미지가 아닌 새 완성 이미지를 배포한 것은 아니며, 현재 checkout 코드와 기존 SDK 조합을 검증했다. source mount를 사용하는 개발 환경에서는 코드가 보이지만 패키지·이미지 교체는 하지 않았다.

## 재현

테스트 서버를 준비한 뒤 저장소 소스가 PYTHONPATH에 보이는 runner에서 실행한다. 인증정보는 임시 테스트 서버 전용 환경변수로 제공한다.

```bash
python -m unittest \
  mage_integrations.tests.destinations.test_delta_lake \
  mage_integrations.tests.destinations.test_delta_lake_s3
```

MinIO 테스트에 필요한 환경변수는 MAGE_TEST_MINIO_ENDPOINT, MAGE_TEST_MINIO_ACCESS_KEY, MAGE_TEST_MINIO_SECRET_KEY다. endpoint가 없으면 MinIO 테스트 5개는 명시적으로 skip된다. 이번 실행에서는 모두 제공하여 skip 없이 통과했다.

임시 로그는 `/tmp/mage-delta-tests.log`, `/tmp/mage-delta-regression.log`, `/tmp/mage-delta-browser.log`에 있다. 테스트용 MinIO·API backend 컨테이너와 전용 네트워크는 검증 후 제거한다. 원본 3100 및 기존 개발 프로젝트는 변경하지 않는다.

## 남은 범위

사내 Ceph/MinIO endpoint·인증정보로의 검증은 하지 않았다. MinIO 검증이 모든 S3 호환 구현의 호환성을 보장하지는 않는다. AWS_S3_ALLOW_UNSAFE_RENAME=true를 유지하므로 단일 writer 기준이며 동시 쓰기는 검증 범위 밖이다.

Couchbase의 libssl.so.1.1 문제는 다음 R3b 대상이다. 의존성 충돌 5건 수정은 사용자 요청대로 보류하고, 이후 upstream Dockerfile 기준 빌드 검증에서 재검토한다.
