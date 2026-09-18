# 기존 Spark UI 복원 — EMR 연결 제외

## 기준

리팩터링 전 `1912c297f`의 UI 소스를 기준으로 복원했다. `KernelStatus.tsx`의 이전 변경 이력 `09565898d`도 확인했다. 새 화면을 설계하는 대신 기존 컴포넌트의 레이아웃·문구·탭·버튼을 유지하고 EMR에 해당하는 부분만 제외한다.

## 복원한 화면

- 편집기 상단 **Compute → Switch to PySpark/Python kernel** 메뉴.
- 오른쪽 Python/PySpark 커널 선택, 상태 아이콘, Spark 애플리케이션 이름·버전 또는 `Compute unavailable` 상태 표시.
- `/compute`의 기존 **Compute management** 화면과 Standalone cluster 선택 카드.
- **Setup**: 애플리케이션 이름, Master URL, Spark home, 사용자 세션, 환경변수, JAR 설정과 저장.
- **Resources**: SparkConf 속성 편집·저장.
- **Monitoring**: 애플리케이션, 작업, SQL 및 기존 작업·스테이지 시각화.
- **System**: Spark 환경과 실행기 정보.

`FileHeaderMenu`와 `/compute` 페이지 진입부는 기준 커밋 소스 그대로 복원했다. 커널 상태 표시와 Spark 설정 화면은 원본에서 EMR 분기를 제외했다. 원래의 `compute_management` 기능 플래그 조건도 유지한다. 편집기의 Compute 메뉴와 Spark 상태 표시는 프로젝트 `metadata.yaml`의 `features.compute_management: true` 조건에서 표시되며, `/compute` 설정 화면은 직접 열 수 있다.

## 제외한 부분

AWS EMR 서비스 선택, 클러스터 생성·선택·종료, AWS 자격증명과 IAM 설정, EC2·보안 그룹·SSH 터널, EMR 부트스트랩 및 원격 연결 상태 UI는 복원하지 않는다. 제거했던 클라우드 실행기·서비스·API 구현도 복원하지 않는다.

Standalone 서비스 상태는 프로젝트 `spark_config`에서 읽는다. 화면이 `compute_services`, `compute_clusters`, `compute_connections`, EMR `clusters` API를 호출하지 않는다. Spark 모니터링은 기존 `spark_*` API를 사용한다.

Spark가 설치되지 않았거나 설정이 없는 환경에서도 설정 화면을 열 수 있도록, 모니터링 API는 `None` 대신 standalone adapter를 사용해 빈 결과를 반환한다. 실행 중인 애플리케이션이 없을 때 `System`의 executor 목록도 오류 없이 비어 있는 상태로 표시한다. API 생성에 전달한 내부 Spark 설정과 Spark UI 주소도 유지한다.

## 검증과 제한

- Spark UI/API·커널·클라우드 제거 관련 Python 테스트 18개 통과.
- 전체 TypeScript 검사 통과.
- 격리된 브라우저 7개 화면 및 Monaco 통과. Setup 값 저장, Resources/Monitoring/System 실제 콘텐츠, Compute 커널 전환 메뉴, Spark 빈 상태 표시, Python↔PySpark 전환·저장·alive 상태를 확인했다.
- 브라우저·백엔드 외부 연결 시도 0건, 클라우드 관리 API 호출 0건, 화면/API 오류 0건.
- 현재 기본 개발 이미지에는 PySpark/Java가 없으므로 실제 Spark 작업 실행과 사내 클러스터 연결은 별도 검증 대상이다. 이번 작업에서 패키지나 이미지는 추가하지 않았다.

개발 환경은 소스 마운트로 반영한다. 배포용 정적 UI와 이미지는 별도 재빌드가 필요하다. GitHub 업로드는 하지 않는다.

## 원본 비교 후 커널 메뉴 표시 수정

0.9.79 원본 화면과 비교하면서 커널 선택 항목의 DOM 차이를 확인했다. 테스트 식별자를 넣기 위해 `label`을 JSX `span`으로 반환하면 `FlyoutMenu`의 문자열 처리 분기를 건너뛰어 원래의 `Flex → Text → span[role="menuitem"]` 구조가 사라진다. 이를 원본과 같은 문자열 반환으로 복원했다. 브라우저 검증 스크립트도 테스트 식별자 대신 `menuitem` 역할과 표시 이름으로 항목을 선택하도록 변경했다. 이 수정은 Python/PySpark 두 항목에 동일하게 적용되며 EMR 제거 동작에는 영향을 주지 않는다.
