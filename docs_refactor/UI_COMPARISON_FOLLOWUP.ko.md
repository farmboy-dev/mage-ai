# UI 비교 보완 및 A+B 적용 기록

**상태:** 아래 조사 이후 사용자가 A+B를 승인했고 적용을 완료했다. C는 후속 계획이며 Compute 배포 라우팅은 계속 보류한다. 조사 시점의 기록과 제안은 아래에 보존하고, 적용·검증 결과는 마지막 절에 기록했다.

2026-09-18. 사용자가 승인한 범위는 비교 조사와 문서 정리다. 이 작업에서 애플리케이션 코드·프로젝트 설정을 수정하지 않았고, 서비스를 활성화하거나 블록 생성·실행·AI 생성·설정 저장을 하지 않았다. 브라우저는 로그인 이외의 변경용 HTTP 요청을 차단하도록 구성했으며, 실제로 차단 대상 요청도 발생하지 않았다. API 키 및 Secrets 입력값은 스크린샷에서 가렸다.

[스크린샷 비교 뷰어](ui_comparison_0979/index.html)에 상세 화면을 추가했다. 기본 조건은 Chromium 1440×1000, 새 브라우저 프로필이다.

## 1. Compute

원본은 내부 라우터로 진입했다. 서버의 `/compute` 직접 접속·새로고침 문제는 요청에 따라 보류하며 이번 변경안에도 포함하지 않는다.

| 항목 | 원본 0.9.79 | 수정본 | 판단 |
|---|---|---|---|
| 서비스 선택 | Standalone cluster, AWS EMR | Standalone cluster | EMR 제거 의도와 일치. Change로 선택 화면만 열었고 Enable은 누르지 않음 |
| Setup 공통 | 앱 이름, Master URL, Spark home, 사용자 세션, 환경변수, JAR | 동일한 기본 항목 | 유지 대상 |
| Setup EMR | Remote variables directory, Bootstrap script path | 없음 | EMR 연계 설정 제거. MinIO/Ceph S3 커넥터 제거와 별개 |
| Resources 공통 | SparkConf key/value 설정 | 유지 | 유지 대상 |
| Resources EMR | SSH/EC2 key, 인스턴스 유형·개수, Master/Slave 설정, 보안 그룹 | 없음 | 의도한 제거 |
| Monitoring | 현재 상태에서 메뉴는 숨겨짐. 내부 이동으로 `?tab=monitoring` 진입 시 Applications·Jobs·SQLs 표시 | 메뉴와 세 하위 항목 표시, 빈 목록의 컬럼도 표시 | 서비스 상태와 API 응답 차이를 포함하므로 완전히 같은 상태의 비교는 아님 |
| System | 내부 이동으로 `?tab=system` 진입 시 Environment·Executors 및 Runtime 등 항목 표시 | 같은 기본 항목 표시 | 실제 Spark 연결 없이 빈 상태 비교 |

원본은 화면상 AWS EMR로 표시되지만 현재 메뉴에는 Setup·Resources만 보였다. 기존 소스의 `buildTabs`는 `computeService.uuid`가 AWS EMR 또는 Standalone일 때 Monitoring·System을 추가한다. 수정본은 프로젝트 Spark 설정으로 Standalone 서비스를 구성하므로 네 메뉴가 나타난다. 화면에 표시되는 서비스 이름과 조회된 서비스 객체에 따른 탭 노출을 구분해야 한다. 이번 조사에서 원본의 설정이나 기능 플래그를 바꿔 상태를 맞추지는 않았다.

**이전 보고 정정:** Change 버튼의 카드 경계 넘침은 원본에서도 재현됐다. 수정본에만 생긴 회귀로 분류하지 않는다. 수정본의 `0 applications`·`0 jobs` 세로 줄바꿈은 여전히 확인되지만 원본의 현재 상태에서는 건수 표시가 없어 같은 조건으로 대조하지 못했다. 관련 코드에는 기본 왼쪽 너비 160px와 건수 영역의 줄바꿈 허용 구조가 남아 있다.

## 2. Secrets

- 원본과 수정본 모두 **파이프라인 편집기 오른쪽 → Secrets**가 있고 실제 패널이 열린다.
- 수정본에는 **메인 왼쪽 메뉴 → Secrets → `/secrets`**라는 별도 관리 화면도 있다. 현재 등록된 Secret은 없는 상태다.
- 두 진입점은 모두 기존 `api.secrets.list`를 사용한다. 메인 메뉴 노출을 없애는 것과 Secrets 저장·조회 기능을 제거하는 것은 별개 작업이다.
- 메인 Secrets 항목은 리팩터링 이전 로컬 HEAD에도 있었으며, 원본 이미지의 페이지 manifest에는 `/secrets`가 없다. 이 차이를 이번 작업에서 새로 추가한 기능으로 설명해서는 안 된다.
- [수정본 메인 Secrets 화면](ui_comparison_0979/modified-global-secrets.png). Secret 생성·수정·삭제는 하지 않았다.

## 3. 커널 및 블록 추가 메뉴

- 커널 선택 메뉴를 양쪽에서 열었다. 선택 항목은 누르지 않았다. 앞선 동일 상태 측정에서는 PySpark 항목의 DOM·스타일이 일치했고, 이번에는 원본 Python / 수정본 PySpark 상태라 반대 커널 이름이 각각 표시됐다.
- Data loader 메뉴는 원본 Python 상태에서 Python·SQL·R·Custom template이, 수정본 PySpark 상태에서 데이터 소스 목록이 바로 나타난다. 소스의 파이프라인 유형 분기에 따른 차이이며, 비교를 위해 커널이나 파이프라인 유형을 바꾸지는 않았다.
- **남아 있는 외부 클라우드 템플릿:** 수정본 메뉴에서 Azure Blob Storage, Google BigQuery, Google Cloud Storage, Google Sheets, Amazon Redshift, Snowflake를 확인했다.
- Amazon S3, Local file, API, 내부 DB 항목도 함께 남아 있다. S3는 MinIO/Ceph 때문에 보존 대상이다. API·DB는 내부 서비스에 사용할 수 있으므로 일괄 제거하면 안 된다.
- 신형 블록 추가 UI는 현재 기능 플래그가 꺼져 있어 실제 화면 비교에서 제외했다. 이번 결과를 모든 블록 종류·모든 템플릿의 전체 검사 결과로 확대하지 않는다.

## 4. AI 설정 및 모달

- 양쪽에서 AI actions 메뉴를 열고 AI가 미설정 상태임을 확인한 뒤 Document block 진입 시의 **설정 모달만** 확인했다. AI 생성 요청은 하지 않았다.
- 원본은 OpenAI API key 등록 안내, 외부 OpenAI 문서, Try Mage Pro 안내를 표시한다.
- 수정본은 OpenAI-compatible base URL·모델 안내와 내부 Preferences 링크를 표시하고, API base URL·Model 입력 및 선택적인 API key 설정을 제공한다.
- 일반 Preferences와 편집기 모달이 같은 설정 컴포넌트를 사용하여 안내 변경이 양쪽에 반영되어 있다. 모달의 Project·Pipeline settings·Features 기본 구조는 유지됐다.
- Features 및 Spark 설정의 외부 문서 링크는 일부 남아 있다. 클릭하지 않았다.

## 승인 대기 변경안

아래는 제안이며 **아직 적용하지 않았다**. 항목별 승인 후 구현한다.

### A. Compute 왼쪽 표시 개선 — 선택 사항

원본부터 존재하는 표시 문제도 포함하므로 “원본 복원”이 아닌 별도 UI 개선으로 승인받는다.

- 대상: `mage_ai/frontend/components/ComputeManagement/index.tsx`, `index.style.tsx`, `constants.tsx`.
- 기본 왼쪽 너비를 160px에서 320px로 조정하고 최소 너비는 280px로 제한한다. 저장된 기존 너비와 드래그 조정에도 같은 하한을 적용한다.
- 서비스 카드 안에서 아이콘·Change 버튼이 겹치거나 카드 밖으로 나가지 않도록 배치한다.
- Monitoring 건수는 줄바꿈되지 않도록 하고 글자 단위 분할을 방지한다.
- 탭 이름·순서·설정 항목·Spark 연결 로직·서버 라우팅은 수정 범위에 포함하지 않는다.
- 검증: 1440px·1024px 화면, 새 프로필·기존 좁은 너비 저장 상태, 네 탭 이동에서 카드 경계와 건수 배치 확인. TypeScript 검사.

### B. Secrets 메인 메뉴 노출을 원본에 맞춤 — 권장

- 대상: `mage_ai/frontend/components/Dashboard/VerticalNavigation.tsx`.
- 메인 왼쪽 메뉴의 Secrets 항목과 사용하지 않게 되는 해당 아이콘 import만 제거한다.
- 편집기 오른쪽 Secrets 패널은 유지한다. `/secrets` 페이지 파일·API·저장된 Secret·암호화·권한 로직은 변경하지 않는다. 메뉴 숨김은 접근 차단이 아니다.
- UI 영향: 메인 메뉴 아이콘 하나가 줄어들고 아래 항목이 위로 이동한다.
- 검증: 메인 메뉴에서 항목 미노출, 편집기 오른쪽 Secrets 패널 진입, 기존 `/secrets` 페이지 유지 확인. 생성·삭제 없이 TypeScript 및 브라우저 확인.

### C. 남은 클라우드 템플릿·커넥터 정리 — 후속 계획

- 아직 구현 승인 요청 대상이 아니다. Azure·BigQuery·GCS·Google Sheets·Redshift·Snowflake의 템플릿, 실제 커넥터, 의존 패키지, 신형 블록 추가 UI까지 연결 관계를 먼저 조사해야 한다.
- UI만 숨길지 실제 기능·패키지까지 제거할지 구분하여 파일별 변경안을 제출한다.
- S3/MinIO/Ceph, OpenAI-compatible AI, PySpark, 내부 API·DB 연결은 보존 조건으로 명시한다.

이번 조사에서 GitHub 업로드·컨테이너 재구성·애플리케이션 코드 변경은 하지 않았다. 문서와 비교 이미지·뷰어만 갱신했다.

## A+B 승인 후 적용 결과

사용자의 “A+B로 진행하자” 승인에 따라 위 네 파일을 수정했다.

- Compute 기본 왼쪽 너비 320px, 최소 280px 적용. 기존 저장값이 160px이어도 화면에서는 280px로 보정한다.
- 드래그 좌표의 기존 오프셋을 보정한 실제 패널 너비를 저장하여, 새로고침 뒤에도 동일한 너비를 유지한다.
- 서비스 카드의 너비를 부모에 맞추고 내부 여백을 포함하도록 했다. 아이콘과 Change 버튼 사이 간격을 두고 버튼이 축소되지 않도록 했다.
- Monitoring 건수 영역이 축소되지 않도록 하고, 두 건수 문구에 줄바꿈 금지를 적용했다.
- 메인 내비게이션의 Secrets 항목과 해당 아이콘 import만 제거했다. 편집기 Secrets 패널·별도 `/secrets` 페이지·API·데이터는 유지했다.

검증 결과:

- 전체 TypeScript 검사 통과.
- Chromium 1440px / 1024px 각각 새 프로필 및 기존 160px 저장 상태, 총 네 조건 통과.
- 각 조건에서 Setup·Resources·Monitoring·System 네 탭의 카드 내부 버튼 배치, 건수 한 줄 표시, 최소 너비를 측정했다.
- 각 조건에서 실제 드래그로 최소 너비 280px를 확인하고 새로고침 후에도 280px가 유지되는 것을 확인했다.
- 메인 Overview에서 Secrets 아이콘 미노출, `/secrets`의 New secret 버튼과 편집기 오른쪽 Secrets 패널 접근 확인. Secret 생성·삭제와 프로젝트 설정 저장은 하지 않았다.

[1440px 적용 화면](ui_comparison_0979/ab-1440-fresh.png) · [1024px / 기존 좁은 너비 적용 화면](ui_comparison_0979/ab-1024-saved.png) · [측정 결과](ui_comparison_0979/ab-results.json)

3000 개발 환경에는 소스 마운트로 반영된다. 배포 이미지 재빌드와 Compute 서버 라우팅 수정은 수행하지 않았다.
