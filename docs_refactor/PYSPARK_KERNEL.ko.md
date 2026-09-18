# EMR 없는 PySpark 커널

클라우드 실행기 제거 과정에서 빠졌던 **Python / PySpark 커널 선택을 복원**했다. PySpark 자체는 EMR과 무관하며 로컬 또는 사내 Spark 클러스터에서 사용할 수 있다.

이후 [기존 Spark UI 복원](SPARK_UI_RESTORATION.ko.md)에서 이전 커밋 기준의 Compute 메뉴·설정·모니터링 화면도 복원했다.

## 동작

- 편집기 오른쪽 커널 메뉴에서 Python ↔ PySpark를 선택한다. 선택은 파이프라인의 `type`으로 저장된다.
- PySpark 커널은 별도 로컬 IPython 프로세스를 실행한다. 기존 sparkmagic/Livy 커널이나 EMR 설정을 조회하지 않는다.
- 노트북 블록과 scratchpad 실행 시 파이프라인 `spark_config`를 우선 사용하고, 없으면 프로젝트 설정을 사용해 `spark` 세션을 준비한다.
- PySpark 파이프라인의 실행 인프라는 `executor_type: local_python` 또는 `k8s`로 설정한다. 커널 종류를 보고 EMR 실행기를 자동 선택하지 않는다.
- 기존 EMR 전용 `executor_type: pyspark`는 계속 차단한다. `type: pyspark`와 다른 설정이다.
- `%%spark`, `%%local` 같은 Livy 전용 셀 매직과 원격 결과 복사 코드는 사용하지 않는다. 일반 PySpark Python 코드를 실행한다.

## 설정 예시

로컬 Spark:

```yaml
type: pyspark
executor_type: local_python
spark_config:
  app_name: internal_pipeline
  spark_master: local[2]
```

사내 Spark 클러스터를 사용하려면 `spark_master`를 `spark://내부호스트:7077` 등 해당 환경의 주소로 변경한다. 필요한 JAR와 Spark 설정도 `spark_config`에 지정한다. Master 설정을 생략하면 `SPARK_MASTER_HOST` 환경변수 또는 기본값 `local`을 사용한다.

**현재 기본 개발 이미지에는 PySpark와 Java가 설치되어 있지 않다.** 커널 선택·전환 자체는 가능하지만 실제 Spark 계산을 하려면 실행 이미지에 두 의존성을 설치해야 한다. Kubernetes 실행 시에는 Pod 이미지에도 필요하다. 이번 수정에서는 이미지나 의존성을 추가하지 않았다. 실제 Spark 버전은 사내 클러스터와 맞춰야 한다.

PySpark 모드에서 의존성이 없거나 Spark 세션 생성에 실패하면 명시적 오류를 표시한다. Python 모드의 기존 선택적 Spark 처리에는 영향을 주지 않는다.

## 검증 범위

- 관련 Python 테스트 29개 및 전체 TypeScript 검사 통과.
- 브라우저 7개 화면, Python ↔ PySpark 양방향 선택·설정 저장·각 커널의 alive 상태 확인. 외부 요청·클라우드 API 호출·화면/API 오류 0건.
- 커널 스펙이 sparkmagic 대신 IPython을 사용하는지 확인.
- 내부 Spark 설정 전달, 셀 매직 제거, 기본 실행기 선택, 잘못된 Spark 설정과 의존성 누락 오류 검증.
- 네트워크가 없는 환경에서 기본 loader → transformer → exporter 실행 통과.
- 실제 Spark 작업 실행과 사내 Spark/Kubernetes 연결은 미검증. 세션 생성은 mock으로 검증했다.

소스 마운트를 사용하는 개발 환경에 반영하며 배포용 정적 UI 및 이미지는 별도 재빌드가 필요하다. GitHub에는 업로드하지 않는다.
