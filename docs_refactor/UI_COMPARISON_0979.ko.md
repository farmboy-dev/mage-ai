# 원본 0.9.79와 수정본 UI 비교

후속 조사와 정정은 [UI 비교 보완](UI_COMPARISON_FOLLOWUP.ko.md)에 기록했다. 원본 Compute 네 화면을 내부 이동으로 확인했고, Change 버튼 넘침은 원본에서도 재현했다. 아래 내용 중 비교 제한은 최초 조사 당시의 기록이다.

2026-09-18 기준, 실제 실행 중인 원본 `3100`과 수정본 `3000`을 Chromium의 동일한 1440×1000 화면 크기에서 비교했다. Overview, Pipelines, example_pipeline 편집기, 파이프라인 설정, Workspace preferences, Compute를 열고 커널 메뉴도 확인했다. 비교 중 설정 저장이나 블록 실행은 하지 않았다.

[원본·수정본 스크린샷 비교 뷰어](ui_comparison_0979/index.html)에서 화면을 선택하면 양쪽 이미지를 나란히 볼 수 있다. HTML 파일과 같은 폴더의 PNG 파일을 함께 유지해야 한다.

## 관찰한 차이

| 위치 | 원본 | 수정본 | 판단 |
|---|---|---|---|
| 공통 헤더 | Live help, Try Pro, 버전 외부 링크 | 도움말·Pro 링크 제거, 버전은 텍스트 | 의도한 외부 링크 제거 |
| 계정 메뉴 | Light mode Pro 링크 | 없음 | 의도한 외부 링크 제거 |
| 왼쪽 내비게이션 | Deploy 아이콘 | 없음 | 의도한 외부 배포 링크 제거 |
| 왼쪽 내비게이션 | Secrets 아이콘 없음 | Secrets 아이콘 있음 | 이미지와 로컬 기준 소스 차이. Secrets 항목은 리팩터링 이전 HEAD에도 존재하며 이번 제거 작업에서 추가한 항목이 아님 |
| Overview / Pipelines | 기존 카드·목록 | 같은 기본 배치 | 확인한 범위에서 헤더·내비게이션과 프로젝트 데이터 외의 배치 차이를 발견하지 못함 |
| 편집기 | 파일 트리·코드·DAG | 같은 기본 배치 | 블록 실행 결과, 커널 상태, 저장 시각이 다름. UI 회귀와 구분 필요 |
| PySpark 선택 항목 | Flex → Text → span[role=menuitem] | 동일 | 이전 JSX label 문제 수정 후 DOM 및 계산된 스타일 일치 |
| 파이프라인 Executor type | Azure, ECS, GCP Cloud Run, k8s, local_python, pyspark | local_python, k8s | 의도한 클라우드 실행기 제거. 이 목록의 pyspark는 기존 EMR 실행기이며 상단 PySpark 커널 메뉴와 별개 |
| Preferences | Help improve Mage 토글 | 없음 | 의도한 통계 전송 UI 제거. 아래 섹션이 위로 이동 |
| Preferences AI | OpenAI API key 중심 | OpenAI-compatible AI, API base URL·Model 입력 추가 | 의도한 내부 AI 설정 지원 |
| Compute 직접 접속 | HTTP 404 | Standalone 설정 화면 표시 | 실제 관찰한 차이. 원본 이미지의 이 경로로는 시각적 동등성 검증 불가 |

## 수정이 필요한 표시 문제

수정본 Compute 화면의 왼쪽 영역에서 `0 applications`, `0 jobs`가 글자 단위로 세로 줄바꿈되고, `Change` 버튼이 카드 밖으로 튀어나온다. 현재 1440×1000, 새 브라우저 프로필에서 재현된다. 너비와 줄바꿈 처리를 점검할 필요가 있다. 이번 작업은 비교·기록만 수행했으며 이를 수정하지 않았다. 원본 화면은 404이므로 원본에도 같은 문제가 있는지는 판단하지 않았다.

## 커널 메뉴 수치 비교

양쪽에서 열린 PySpark 메뉴 항목의 계산된 스타일과 위치를 측정했다.

- 글꼴: `Roboto Regular`, `Helvetica Neue`, Helvetica, sans-serif
- 크기 / 굵기 / 행 높이: 14px / 400 / 20px
- 색상: rgb(255, 255, 255)
- 텍스트 영역: x=720, y=126.5, width=52, height=16
- 부모 요소: P, 그 부모: DIV

모두 일치했다. 측정값은 [JSON](ui_comparison_0979/kernel-menu-metrics.json)에 저장했다. styled-components의 해시 클래스명 자체는 개발 빌드와 배포 빌드에서 다를 수 있으므로 동일성 판단 기준으로 사용하지 않았다.

## 비교 제한과 남은 항목

- 원본은 배포 이미지, 수정본은 로컬 소스의 개발 빌드다. 동일한 버전 표시만으로 모든 화면이 같은 기준 소스라고 볼 수 없다. Secrets 메뉴 차이도 이 구분이 필요한 사례다.
- 독립 프로젝트이므로 UUID, 저장 시각, 실행 결과, 커널 상태가 다르다. 촬영 도중에도 수정본 커널 상태가 달라졌으므로 이 상태 차이를 디자인 변경으로 분류하지 않았다.
- 첫 수정본 편집기 촬영은 Monaco 코드 표시가 완료되기 전이었다. 다시 기다린 촬영에서는 코드가 정상 표시됐고 양쪽 모두 첫 에디터의 코드 행 28개를 확인했다. 비교 뷰어는 재촬영본을 사용한다.
- 확인한 화면에서 브라우저 JavaScript 예외는 발생하지 않았다. 전체 API·외부 통신·모든 모달·반응형 크기를 검사한 결과는 아니다.
- Preferences의 `Features (docs)` 등 외부 문서 링크는 여전히 보인다. 외부 링크까지 전부 없어진 상태는 아니다.
- Compute의 네 탭은 원본 이미지와의 대조가 완료되지 않았다. 아래 후속 조사에서 직접 접속과 클라이언트 이동의 차이를 확인했다.

## 후속 확인: 원본 Compute의 404 원인

원본 이미지에도 `frontend_dist/compute.html`, `chunks/pages/compute-9e2dea78024e3bb4.js`가 존재하고 Next.js 빌드 manifest에도 `/compute`가 등록되어 있다. 반면 Python Tornado 서버의 페이지 라우팅 목록에는 `/compute`가 없다.

- 원본 3100(Python 서버): `/compute` 직접 요청 HTTP 404.
- 수정본 6789(Python 서버): 동일하게 HTTP 404.
- 수정본 3000(Next.js 개발 서버): 페이지 파일을 자동으로 라우팅하여 HTTP 200.
- 원본에서 로그인 후 브라우저의 Next.js 라우터로 `/compute`에 이동하면 **Compute management 화면이 실제로 표시된다**. 이때 AWS EMR, Remote variables directory, Bootstrap script path 등 원본 설정 항목도 확인했다. 프로젝트 설정은 저장하지 않았다.

따라서 원본에 Compute 화면이 없는 것이 아니라, 서버의 직접 URL 처리에 해당 경로가 빠져 있는 문제다. 브라우저 내부 이동과 직접 접속·새로고침을 구분해야 한다. 위 비교 뷰어의 원본 Compute 스크린샷은 직접 접속 시의 404를 기록한 것이다. 이 확인으로 기존의 “원본 화면을 볼 수 없어 비교 불가” 제한은 해소되었지만, 네 탭의 전체 시각 대조는 아직 수행하지 않았다.
