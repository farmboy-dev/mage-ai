# 사내 사용을 위한 Mage 리팩터링 문서

문서 안의 실행 명령과 코드 경로는 별도 안내가 없으면 저장소 루트를 기준으로 한다.

| 문서 | 내용 |
|---|---|
| [경량화 분석](OFFLINE_SLIMMING_ANALYSIS.ko.md) | 최초 분석과 제거·보존 대상, 단계별 계획 |
| [로컬 이미지 빌드](LOCAL_BUILD.ko.md) | 로컬 소스 기반 이미지 빌드와 기본 검증 |
| [개발 환경](DEV_SETUP.ko.md) | 개발 컨테이너 실행, 사내망 접속, 소스 변경 반영 |
| [내부 S3·AI 연결](INTERNAL_SERVICES.ko.md) | MinIO/Ceph 및 OpenAI 호환 API 설정과 검증 |
| [자동 외부 통신 제거](OFFLINE_RUNTIME.ko.md) | 통계·버전 조회·모니터링 정리와 오프라인 검증 |
| [클라우드 실행·UI 제거](CLOUD_EXECUTION_REMOVAL.ko.md) | 실행기·EMR 관리·Secrets Manager 제거, 이전 방법과 검증 |
| [PySpark 커널 복원](PYSPARK_KERNEL.ko.md) | EMR 없는 Python/PySpark 선택과 실행 설정 |
| [기존 Spark UI 복원](SPARK_UI_RESTORATION.ko.md) | 이전 커밋 기준 화면 복원, EMR 연결만 제외 |
| [0.9.79 원본 이미지 실행](ORIGINAL_IMAGE.ko.md) | 3100 포트 비교 환경과 CPU 호환 설정 |
| [원본·수정본 UI 비교](UI_COMPARISON_0979.ko.md) | 실제 화면 비교, 의도한 차이·표시 문제·스크린샷 |
| [UI 비교 보완·A+B 적용](UI_COMPARISON_FOLLOWUP.ko.md) | 상세 비교, Compute 배치 개선·Secrets 메뉴 정리와 검증 결과 |
| [클라우드 커넥터 제거 계획](CLOUD_CONNECTOR_REMOVAL_PLAN.ko.md) | C1~C3 단계, 파일별 변경·보존 대상, 의존성 및 승인 범위 |
| [C1 전용 파일 후보](CLOUD_CONNECTOR_C1_FILES.ko.md) | 여섯 공급자 관련 실제 파일 81개 목록 |
| [C1 제거 결과](CLOUD_CONNECTOR_C1_REMOVAL.ko.md) | 승인된 커넥터 제거, 기존 설정 오류 처리, 보존 범위와 검증 |
| [C2a Algolia·Airtable 제거안](ALGOLIA_AIRTABLE_REMOVAL_PLAN.ko.md) | 승인된 파일별 변경·의존성·검증 범위 |
| [C2a Algolia·Airtable 제거 결과](ALGOLIA_AIRTABLE_REMOVAL.ko.md) | 구현·UI/API 검증 결과와 패키지 정리의 한계 |
| [C2b 런타임 제거안](CLOUD_RUNTIME_C2B_PLAN.ko.md) | GCS 결과·로그 및 Azure/AWS Secrets 제거 범위와 검토 요청 |
| [C2b 런타임 제거 결과](CLOUD_RUNTIME_C2B_REMOVAL.ko.md) | GCS 저장·로그, 클라우드 Secrets 제거 및 이전·검증 결과 |
| [C2c 클라우드 스트리밍 제거안](CLOUD_STREAMING_C2C_PLAN.ko.md) | 5개 서비스, 21개 파일 및 UI·실행 전 검증 변경안 |
| [C2c 스트리밍 제거 결과](CLOUD_STREAMING_C2C_REMOVAL.ko.md) | 21개 전용 파일 제거·연결 전 차단·UI/API 검증 |
| [C2d Google integration 제거안](GOOGLE_INTEGRATIONS_C2D_PLAN.ko.md) | Ads·Analytics·Search Console의 33개 파일 및 UI/API 제거 범위 |
| [C2d Google integration 제거 결과](GOOGLE_INTEGRATIONS_C2D_REMOVAL.ko.md) | 33개 파일 제거·기존 설정 차단·UI/API 검증 |
| [잔여 integration 확인](REMAINING_INTEGRATIONS_AUDIT.ko.md) | 실제 Sources/Destinations 화면의 외부 서비스 잔존과 내부 endpoint 구분 |
| [C2e 잔여 SaaS integration 제거안](SAAS_INTEGRATIONS_C2E_PLAN.ko.md) | 23개 source·Salesforce destination, 공통 테스트·의존성·보존 범위 |
| [C2e 전용 파일 목록](SAAS_INTEGRATIONS_C2E_FILES.ko.md) | 삭제 승인 후보 593개 파일 전체 목록 |
| [C2e SaaS integration 제거 결과](SAAS_INTEGRATIONS_C2E_REMOVAL.ko.md) | 593개 파일 제거·96개 테스트·기존 Couchbase/Delta Lake 호환성 문제 |
| [Tableau·Teradata 추가 제거](TABLEAU_TERADATA_REMOVAL.ko.md) | 사용자 요청에 따른 전용 파일 16개·UI/API 제거 및 검증 |

최초 분석 이후의 구현 상태와 검증 결과는 각 작업 문서를 참고한다. 후속 리팩터링 문서도 이 폴더에 추가한다.
