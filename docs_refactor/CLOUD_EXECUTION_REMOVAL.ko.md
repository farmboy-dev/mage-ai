# 클라우드 실행·설정·UI 제거

## 범위

이번 단계는 실행 인프라와 AWS Secrets Manager를 정리한다. 모든 외부 데이터 커넥터와 SDK를 제거한 상태는 아니다.

| 대상 | 처리 |
|---|---|
| AWS ECS, AWS EMR, GCP Cloud Run, Azure Container Instances 실행기 | 구현과 실행기 분기 삭제 |
| ECS/Cloud Run 워크스페이스 관리 | 구현 삭제, Kubernetes만 허용 |
| EMR 클러스터 생성·관리, SSH 터널, 부트스트랩·실행 템플릿 | 삭제 |
| 클라우드 compute API | 기존 URL은 제거 안내 오류를 반환하는 호환 처리만 유지 |
| 프로젝트의 ECS/EMR/Cloud Run/ACI 설정 | 로딩·API 노출·저장 대상에서 제거 |
| AWS Secrets Manager | 서비스 구현 및 `aws_secret_var` 템플릿 함수 삭제 |
| UI | 실행기 선택을 Local Python/Kubernetes로 축소, EMR 설정·클러스터 선택 제거. Python/PySpark 커널 선택 유지 |
| `/compute` | [기존 Spark UI 복원](SPARK_UI_RESTORATION.ko.md): Standalone 설정·모니터링 유지, EMR 연결만 제거 |

S3용 boto3와 MinIO/Ceph 연결, 내부 OpenAI 호환 AI, 로컬 Python, Kubernetes 실행 및 워크스페이스는 유지한다. Spark 설정과 작업·스테이지·SQL 시각화용 공용 컴포넌트도 유지한다.

## 기존 프로젝트 이전

기존 프로젝트 파일을 일괄 수정하거나 삭제하지 않는다. 예전 `emr_config` 등이 YAML에 있어도 프로젝트를 열 수 있지만, 런타임에서 읽거나 API 응답에 노출하지 않는다. 코드에서 제거된 설정을 새로 저장하면 오류가 난다.

`ecs`, `gcp_cloud_run`, `azure_container_instance`, `pyspark` 실행기는 파이프라인·블록·`DEFAULT_EXECUTOR_TYPE` 어디에 지정되어도 실행 시 오류를 낸다. 제거된 실행기를 자동으로 로컬 실행으로 바꾸지 않는다. API에서 해당 실행기를 새로 지정하는 것도 차단한다.

기존 `executor_type: pyspark` 실행기는 EMR 전용이었다. `type: pyspark` 파이프라인과 UI의 PySpark 커널은 유지하며, EMR 없이 로컬 IPython 커널에서 실행한다. 상세 변경은 [PySpark 커널 복원](PYSPARK_KERNEL.ko.md)을 참고한다. 내부 Spark로 이전할 때는 다음을 함께 변경한다.

1. PySpark 파이프라인은 `type: pyspark`를 유지하거나 UI 커널 메뉴에서 PySpark를 선택한다.
2. 파이프라인과 각 블록의 제거된 `executor_type`을 `local_python` 또는 `k8s`로 변경한다. `DEFAULT_EXECUTOR_TYPE`도 확인한다.
3. EMR 전용 `executor_config`는 정리하고 내부 Spark 설정을 `spark_config`에 넣는다.
4. 실행 환경에 PySpark, 호환 Java, 필요한 JDBC/JAR를 사내 배포 경로로 준비한다.

예시:

```yaml
type: pyspark
executor_type: local_python
spark_config:
  app_name: internal_pipeline
  spark_master: spark://internal-spark:7077
  others:
    spark.sql.shuffle.partitions: '2'
```

Spark 설정은 프로젝트 `metadata.yaml`에도 둘 수 있다. 실제 호스트·포트·리소스 설정은 사내 환경에 맞게 변경한다. 개발 이미지에는 현재 PySpark와 Java가 없으므로 위 설정만으로 Spark 실행이 가능해지는 것은 아니다.

AWS Secrets Manager에서 가져오던 값은 환경변수나 Mage 내부 secret으로 옮긴다. DB는 `MAGE_DATABASE_CONNECTION_URL` 또는 기존 Postgres 환경변수를 사용한다. DB URL이 별도로 지정되지 않은 상태에서 `AWS_DB_SECRETS_NAME`을 사용하면 제거 안내 오류를 반환한다.

## 검증

- S3·내부 AI·자동 외부 전송 차단 기존 테스트: 14개 통과.
- 클라우드 제거 회귀 테스트: 9개 통과. 제거된 실행기의 각 진입점, API 저장 차단, 클라우드 API, 기존 설정, Secrets Manager, 로컬/Kubernetes dispatch, Spark 설정 전달을 확인했다.
- 전체 TypeScript 검사 통과.
- 내부 전용 Podman 네트워크에서 브라우저 7개 화면(로그인, 프로젝트 설정, 개요, compute 안내, 파이프라인 목록·설정·편집기) 통과. Monaco 표시와 실행기 선택지 확인. 외부 요청·클라우드 API 호출·JavaScript 오류·API 오류 모두 0건. 기존 EMR 설정과 compute 기능 플래그를 넣은 프로젝트로 검증했다.
- 클라우드 API 4개 경로를 직접 호출하여 제거 안내와 `error.code: 400` 확인. 기존 Mage 응답 규약상 HTTP status는 200이며 오류는 JSON 본문에 담긴다. Python 커널 API 정상 응답 확인.
- 네트워크가 없는 컨테이너에서 로컬 loader → transformer → exporter 실행 및 서버 기본 응답 통과. Python 네트워크 감사에서 외부 연결 시도 없음.
- Kubernetes는 실행기 선택·생성 경로를 mock으로 검증했다. 실제 사내 클러스터의 Pod 실행은 검증하지 않았다.
- Spark는 설정 전달 경계를 mock으로 검증했다. PySpark/Java 미설치 및 사내 endpoint 미제공으로 실제 Spark 작업 실행은 검증하지 않았다.

재실행:

```bash
podman run --rm --network none -v "$PWD:/workspace:ro" -w /tmp -e ENV=test \
  localhost/mage-fork-dev:backend python -m unittest \
  mage_ai.tests.data_preparation.executors.test_cloud_removed \
  mage_ai.tests.ai.test_openai_compatible \
  mage_ai.tests.services.aws.s3.test_compatible \
  mage_ai.tests.usage_statistics.test_disabled

podman exec mage-fork-dev_app_1 yarn tsc --noEmit --incremental false
```

## 남은 작업

클라우드 데이터 커넥터, 알림 연동, Azure Key Vault 등은 후속 정리 대상이다. 공유 의존성을 검토한 뒤 requirements와 이미지 패키지를 줄여야 한다. 이번 변경으로 소스는 줄었지만, 기존 개발 기반 이미지의 패키지나 이미지 크기는 아직 줄어들지 않는다.

변경은 소스 마운트를 사용하는 개발 환경에 적용한다. 저장소의 기존 정적 UI 번들과 배포 이미지는 재빌드하지 않았으므로, 배포하려면 프론트엔드 및 이미지를 새로 빌드해야 한다. GitHub 업로드는 하지 않는다.
