# MinIO/Ceph S3와 내부 AI 설정

이번 단계는 남길 내부 서비스 연결 경로를 정리한다. 실제 사내 endpoint·인증 정보는 입력하지 않았으며, 검증은 네트워크가 차단된 컨테이너 안의 로컬 HTTP 대체 서버로 수행했다. GitHub push나 배포 이미지 발행은 하지 않았다.

## 내부 OpenAI 호환 AI

개발 UI의 **Settings → Workspace → Preferences → OpenAI-compatible AI**에서 다음을 저장한다.

- API base URL: 예시 `http://ai.internal:8000/v1`. Mage 백엔드에서 접근 가능한 주소를 입력한다.
- Model: 내부 서버에서 제공하는 정확한 모델 ID.
- API key: 인증이 필요할 때 입력한다. 인증 없는 서버는 비워둘 수 있다.

AI base URL과 모델을 모두 설정해야 AI 생성 기능을 사용할 수 있다. 연결 확인 버튼이나 모델 자동 조회는 아직 없다. UI의 준비 상태는 설정 유효성만 의미하며 실제 연결 성공 판정은 아니다. 기존에 API key만 저장해 사용하던 프로젝트도 주소와 모델을 추가해야 한다.

주소나 모델을 지정하지 않으면 요청 전에 오류를 반환한다. 공개 OpenAI 주소나 `gpt-4o` 모델로 자동 대체하지 않는다. 사용자가 명시한 주소를 사용하므로 이 설정 자체가 외부 도메인을 차단하는 네트워크 정책은 아니다.

`metadata.yaml`로도 설정할 수 있다.

```yaml
openai_base_url: http://ai.internal:8000/v1
openai_model: internal-model
# 인증이 필요한 경우에만 설정
# openai_api_key: ...
```

기존 중첩 설정 `ai_config.open_ai_config`에도 같은 세 필드를 지원한다. 설정 우선순위는 **프로젝트 최상위 필드 → ai_config.open_ai_config → 환경변수**다. 환경변수는 `OPENAI_BASE_URL`, `OPENAI_MODEL`, `OPENAI_API_KEY`다. `compose.dev.yml`은 호스트 환경변수를 백엔드로 전달하며, 변경 후 `podman-compose -f compose.dev.yml up -d --force-recreate server`로 반영한다. 설정 파일과 환경변수의 값을 혼용하면 필드별로 이 우선순위를 적용한다.

텍스트/코드 생성과 블록 분류는 모두 설정한 서버의 `/chat/completions`를 사용한다. 블록 자동 분류에는 `tools`와 지정한 `tool_choice`를 처리하는 모델/서버가 필요하다. 단순히 채팅 API만 제공하는 서버에서는 해당 기능이 제한된다. 요청 형식은 [공식 OpenAI Chat Completions 문서](https://developers.openai.com/api/reference/cli/resources/chat/subresources/completions)를 참고했다. 인증 없는 서버에는 SDK 요구에 맞춰 `not-required` 토큰을 사용한다. Hugging Face 등 다른 AI 경로는 이번 단계에서 제거하지 않았다.

## 일반 S3 로더·익스포터

프로젝트의 `io_config.yaml`에 전용 프로필을 추가하고 S3 블록의 `config_profile`을 선택한다. UI의 파일 편집기에서 수정할 수 있다.

```yaml
version: 0.1.1
minio:
  AWS_ENDPOINT: http://minio.internal:9000
  AWS_S3_ADDRESSING_STYLE: path
  AWS_REGION: us-east-1
  AWS_ACCESS_KEY_ID: "{{ env_var('AWS_ACCESS_KEY_ID') }}"
  AWS_SECRET_ACCESS_KEY: "{{ env_var('AWS_SECRET_ACCESS_KEY') }}"
  AWS_SESSION_TOKEN: null
```

Ceph RGW도 해당 endpoint와 region을 입력하는 방식이 같다. bucket은 미리 준비하고 로더/익스포터 블록에 지정한다. 새 프로젝트의 기본 IO 설정 템플릿에도 endpoint와 addressing style 항목을 추가했다. 기존 프로젝트의 설정 파일은 자동으로 덮어쓰지 않는다.

```python
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.s3 import S3

storage = S3.with_config(ConfigFileLoader('io_config.yaml', 'minio'))
df = storage.load('data-bucket', 'input.csv')
storage.export(df, 'data-bucket', 'output.csv')
```

`AWS_S3_ADDRESSING_STYLE`은 `path`, `virtual`, `auto`를 지원한다. 사용자 지정 endpoint가 있고 별도 지정이 없으면 path-style을 사용한다. SigV4 서명을 사용하며 TLS 검증을 끄지 않는다. 사내 CA가 필요하면 CA 파일을 컨테이너에 마운트하고 `AWS_CA_BUNDLE`을 별도 전달한다.

## S3 변수 저장소·로그·스트리밍

공통 S3 클라이언트와 일반 IO는 명시적 endpoint 다음으로 `AWS_ENDPOINT_URL_S3`, `AWS_ENDPOINT` 환경변수를 확인한다. 기존 boto3 1.26에서도 `AWS_ENDPOINT_URL_S3`가 적용되도록 Mage에서 직접 전달한다.

원격 변수 저장소:

```yaml
# metadata.yaml
remote_variables_dir: s3://data-bucket/mage-variables
```

이 경로에는 백엔드 환경변수로 endpoint와 자격증명을 전달한다. `compose.dev.yml`은 `AWS_ENDPOINT_URL_S3`, `AWS_S3_ADDRESSING_STYLE`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_DEFAULT_REGION`을 전달한다. 각 작업을 별도 컨테이너에서 실행하면 그 컨테이너에도 같은 설정이 필요하다.

S3 로그 설정의 `destination_config`와 스트리밍 S3 sink는 `endpoint_url`, `region_name`, `aws_access_key_id`, `aws_secret_access_key`, `aws_session_token`, `addressing_style`을 지원한다. 기존 bucket/prefix 설정과 함께 사용한다. 스트리밍 블록 템플릿에도 해당 입력 항목을 추가했다.

기존 S3 서비스 클라이언트의 다운로드가 새 AWS 기본 resource를 만들던 동작을 수정해 이미 구성한 클라이언트를 사용한다. `resource()`도 같은 endpoint/인증 설정을 유지한다. 테스트 등에서 클라이언트를 주입할 때 불필요한 boto3 연결을 생성하던 동작도 제거했다.

## Data Integration S3 커넥터

Source/Destination의 Amazon S3 설정 편집기에서 다음 항목을 사용한다. 커넥터 식별자는 기존 파이프라인 호환성을 위해 `amazon_s3`를 유지한다.

```json
{
  "aws_endpoint": "http://minio.internal:9000",
  "aws_s3_addressing_style": "path",
  "aws_region": "us-east-1",
  "aws_access_key_id": "YOUR_ACCESS_KEY",
  "aws_secret_access_key": "YOUR_SECRET_KEY",
  "aws_session_token": null,
  "bucket": "data-bucket"
}
```

위 설정은 연결 부분만 보여준다. 소스의 prefix/file_type 및 대상의 table/object_key_path 등 기존 작업별 설정도 필요하다. 두 커넥터의 새 설정 템플릿에 endpoint, path-style, session token을 추가했다. 기존 커넥터 설정은 자동 변경하지 않는다. 사내 스토리지는 access/secret key를 지정하고 AWS `role_arn` 경로를 사용하지 않는다. STS 역할 인수 및 AWS 기본 endpoint 경로의 제거는 후속 클라우드 정리 단계에 포함한다.

## 검증 결과와 남은 범위

2026-09-18 개발 환경에서:

- 새 AI/S3 검사 및 기존 S3·스트리밍 검사 14개, Project API 검사 9개, S3를 상속하는 B2 회귀 검사 17개 통과.
- 내부 AI 모의 HTTP 서버로 채팅·tool 호출의 경로/모델/응답 처리 확인. 주소 누락 시 SDK 클라이언트를 생성하지 않는 것 확인.
- S3 모의 HTTP 서버로 CSV 업로드/읽기/파일 다운로드, JSON 변수 저장, 스트리밍 업로드 및 SigV4/path-style 확인. Integration 클라이언트의 endpoint/session token 전달 확인.
- 네트워크 차단 상태에서 기본 프로젝트 생성·서버 응답·로드 → 변환 → 저장 스모크 테스트 통과.
- Chromium에서 AI 설정 화면 렌더링·저장 payload·재조회 후 표시 확인. 브라우저 검사는 격리된 모의 API를 사용했고 실제 실행 프로젝트의 설정은 변경하지 않았다. 실제 저장은 위 Project API 테스트로 별도 검증했다.
- Next 개발 서버 컴파일 및 전체 `tsc --noEmit --incremental false` 통과. 기존 Monaco 예제는 인스턴스를 인자로 받도록 수정했고, 서버 모델에 있는 실행 결과 type/status를 UI 타입에도 반영했다. 새 AI 입력란에서 사용하는 id 속성도 공통 입력 컴포넌트 타입에 추가했다.
- 후속 점검에서 boto3 Config의 부분 S3 옵션 병합 시 path-style이 유실되던 경우를 수정하고 회귀 검사 추가. 잘못된 AI 포트·공백 포함 주소를 준비 상태에서 제외하고, 줄바꿈 없는 JSON 코드 펜스 및 tool 미지원 응답 처리 확인. 총 40개 테스트를 한 번에 실행해 통과했다.

실제 MinIO/Ceph와 사내 모델의 기능·인증·TLS·tool 지원은 접속 정보가 준비되면 별도 검증해야 한다. PySpark/DeltaLake 등 별도 S3 엔진의 설정 경로는 이번 범위에 포함하지 않았다. AWS 기본 연결, STS, 클라우드 기능/의존성은 아직 남아 있다. 통계 전송·버전 확인 및 관련 UI의 후속 제거 결과는 [OFFLINE_RUNTIME.ko.md](OFFLINE_RUNTIME.ko.md)를 참고한다.

재현 명령(저장소 루트):

```bash
podman run --rm --network none -v "$PWD:/workspace:ro" -w /tmp \
  -e ENV=test localhost/mage-fork-dev:backend python -m unittest \
  mage_ai.tests.ai.test_openai_compatible \
  mage_ai.tests.services.aws.s3.test_compatible \
  mage_ai.tests.services.aws.s3.test_s3 \
  mage_ai.tests.streaming.sinks.test_amazon_s3 \
  mage_ai.tests.api.endpoints.test_projects \
  mage_ai.tests.io.test_backblaze_b2
```

개발 서버는 소스 마운트로 변경이 반영된다. 배포용 정적 UI와 실행 이미지는 이번 단계에서 새로 빌드하지 않았다. 배포 전에는 UI 정적 산출물 재생성과 이미지 재빌드가 필요하다.

## Delta Lake S3

R3a에서 Delta Lake S3 destination에도 내부 endpoint 설정을 연결했다. 일반 Amazon S3 connector와 별개로 다음 키를 설정한다.

| 키 | 설정 |
|---|---|
| `aws_endpoint` | MinIO/Ceph의 전체 endpoint URL |
| `aws_s3_addressing_style` | 일반적인 내부 구성은 `path` |
| `aws_allow_http` | HTTP 테스트 서버인 경우에만 boolean `true`, 기본 false |
| `aws_access_key_id`, `aws_secret_access_key` | 저장소 인증정보 |
| `aws_session_token` | 임시 자격증명 사용 시 선택 |
| `aws_region` | 해당 저장소의 서명 region |
| `bucket`, `object_key_path`, `table` | 기존 bucket과 테이블 저장 prefix/name |

boto3와 delta-rs에 동일 설정을 전달한다. HTTPS 인증서 검증을 끄는 옵션은 추가하지 않았다. 실제 사내 인증정보는 채팅 대신 프로젝트 설정/비밀값 관리 경로에 넣는다.

partition 설정이 있으면 overwrite는 입력 batch의 partition 조합만 교체하고 나머지를 보존한다. 빈 batch는 기존 테이블을 지우지 않는다. Delta log 없이 기존 객체만 있는 경로는 삭제하지 않고 실패하므로 새 빈 경로를 지정한다. SDK 0.20.2 제약 때문에 큰따옴표를 포함한 partition 컬럼명은 overwrite 전에 거절한다.

단일 writer 기준이다. 기존 unsafe rename 설정을 유지하므로 다중 writer 동시 쓰기 지원을 보장하지 않는다. [MinIO 검증 결과](DELTA_LAKE_R3_RESULT.ko.md)를 참고한다. Ceph 실서비스 연결 검증은 별도로 필요하다.
