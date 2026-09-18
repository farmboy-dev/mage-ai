# C1 클라우드 커넥터 제거 결과

2026-09-18. 사용자가 승인한 C1 구현을 완료했다. 코드·주석·새 오류 메시지·테스트는 영어로 작성했다. 소스는 로컬에만 반영했으며 GitHub 업로드와 배포 이미지 재빌드는 하지 않았다.

## 제거한 기능

Azure Blob Storage, BigQuery, Google Cloud Storage, Google Sheets, Redshift, Snowflake의 기본 연결 기능을 정리했다.

- [승인 목록의 전용 파일 81개](CLOUD_CONNECTOR_C1_FILES.ko.md) 제거. I/O 구현, SQL 보조 구현, loader/exporter/sensor 템플릿, integration source/destination/connection, Azure·GCS Delta Lake 템플릿 및 Delta Lake Azure destination 포함.
- 추가로 승인 범위의 GCS streaming sink 구현 제거. BigQuery·Redshift·Snowflake GenericIO sink 등록·분기 제거.
- 기존·신형 블록 추가 UI의 공통 목록, SQL 공급자 API, integration source/destination 카탈로그, 기본 템플릿·검색 등록 정리.
- 기존 검색 캐시가 남아 있어도 제거된 **기본** 템플릿은 검색 결과에서 제외. 사용자 작성 블록과 custom template은 일괄 삭제하거나 숨기지 않음.
- 신규 프로젝트용 `io_config.yaml`에서 제거 공급자의 예시 설정 제거. 기존 사용자 프로젝트 설정 파일은 변경하지 않음.
- 삭제된 구현만 검증하던 BigQuery I/O 및 integration 전용 테스트 제거. 템플릿·GenericIO 공통 테스트는 S3·Postgres·내부 DB 검증을 유지하고 제거 대상 오류 검증으로 변경.

## 오류 처리와 기존 프로젝트

`shared/cloud_features.py`의 공통 검증을 템플릿 생성, 블록 생성·변경·실행, SQL 실행, integration 동적 import·파일 경로 계산, streaming sink factory에 연결했다.

오류 예:

```text
Connector 'bigquery' has been removed from this internal deployment. Use a supported internal connector or S3-compatible storage.
```

- 블록 API에서 제거 대상의 신규 설정 요청은 API 오류 코드 400으로 거절한다. Mage의 기존 API 규약에 따라 HTTP 응답이 200이어도 JSON의 `error.code`는 400일 수 있다.
- integration의 포괄적 예외 처리로 제거 오류가 숨겨져 삭제된 파일 경로로 fallback하지 않도록, 경로 계산 전에 검증한다.
- 테스트용 기존 파이프라인에 제거 공급자를 기록한 뒤 조회 및 커넥터 설정과 관계없는 블록 수정이 가능한 것을 확인했다.
- 제거된 커넥터 설정을 신규 지정하거나 다시 전달하는 변경, 또는 실행은 거절된다. 기존 설정·사용자 코드의 자동 변환은 하지 않는다.
- 임의 Python 코드에서 삭제된 모듈을 직접 import하는 경우에는 ImportError가 발생할 수 있다. 커스텀 코드 전체의 네트워크 접근을 차단하는 기능은 아니다.
- 일부 enum·설정 식별자는 과거 메타데이터 해석과 기존 화면 호환성을 위해 남긴다. 활성 카탈로그·실행 지원과 구분한다.

## 보존한 기능과 이번 범위 밖

- S3/MinIO/Ceph I/O·integration·센서·로그·중간 결과 저장·streaming sink·S3 Delta Lake 유지.
- OpenAI 호환 내부 AI, Python/PySpark 커널, Spark·내부 SQL·API·로컬 파일 기능 유지.
- C2 대상인 GCS 로그·중간 결과 저장, Key Vault·AWSSecretLoader 잔여 구현, 나머지 클라우드 streaming·SaaS는 남아 있다. GCS 전체 기능 제거가 완료된 것은 아니다.
- C3 패키지와 클라우드 dbt 어댑터는 아직 제거하지 않았다. 클라우드 SDK가 설치되어 있으며 사용자 코드에서 직접 이용할 수도 있다. 이번 결과를 이미지 경량화 완료나 외부 통신의 전면 차단으로 해석하지 않는다.
- Compute 배포 라우팅은 계속 보류한다. Secrets 및 Compute A+B 레이아웃을 다시 변경하지 않았다.

## 검증 결과

- Python 57개 테스트 통과: 제거 정책·카탈로그·기본 템플릿 파일 존재 여부·동적 import 전 차단·SQL/streaming 실행 전 차단·검색 캐시·기존 템플릿·GenericIO·S3 호환·내부 AI·PySpark 커널·Spark UI·기존 클라우드 실행기 제거 회귀.
- 전체 TypeScript 검사 통과. 변경된 Python 파일 구문 검사 및 diff 공백 검사 통과.
- 격리된 테스트 서버에서 SQL 공급자 9개, integration source 40개, destination 15개 반환 확인. 제거 대상 UUID가 없고 S3·내부 공급자가 남아 있음.
- BigQuery data source, Snowflake SQL provider, GCS Delta Lake template path를 직접 요청한 세 경우 모두 API 오류 코드 400. 거절된 블록이 저장되지 않은 것도 확인.
- 기존·신형 블록 추가 UI의 Data loader 메뉴를 실제 브라우저로 확인. 두 화면 모두 제거 대상이 없고 Amazon S3가 표시되며 JavaScript 예외 0건. 모든 메뉴의 모든 상호작용을 검사한 것은 아니며 공통 카탈로그·템플릿 검증을 함께 수행했다.
- 테스트용 legacy 파이프라인 조회 및 커넥터 외 필드 수정 통과.
- 격리 서버의 네트워크 감사에서 외부 연결 시도 0건. 실제 사내 MinIO/Ceph·AI·Spark endpoint는 제공되지 않아 검증하지 않음.

기존 PostgreSQL 템플릿 테스트에는 현재 템플릿에 없는 `loader.commit()` 기대값이 남아 있었다. 실제 템플릿은 변경하지 않고 오래된 테스트 기대값만 정리했다.

[기존 UI](cloud_connector_c1/menu-v1.png) · [신형 UI](cloud_connector_c1/menu-v2.png) · [브라우저 검증 기록](cloud_connector_c1/browser-results.json)

검증 후 수정본 개발 서버를 재시작했고 6789 상태 API의 HTTP 200 응답을 확인했다. 3000 개발 화면에 반영된다. 3100 원본 컨테이너와 사용자 프로젝트는 유지했으며, 격리 테스트 서버는 삭제했다.
