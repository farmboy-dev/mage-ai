# Mage 0.9.79 원본 이미지 비교 실행

수정한 개발 환경과 비교하기 위한 별도 컨테이너다. Docker Hub의 `docker.io/mageai/mageai:0.9.79`를 사용하며 저장소 소스를 마운트하지 않는다.

- 컨테이너: `mage-original-0979`
- 포트: 호스트 `3100` → 컨테이너 `6789`
- 접속: `http://172.16.0.134:3100` 또는 서버의 `http://127.0.0.1:3100`
- 데이터 볼륨: `mage-original-0979_data`
- 기존 개발 환경: `3000` / `6789` 그대로 유지

이 서버는 AVX 명령어를 지원하지 않아 이미지에 포함된 Polars 실행 시 `SIGILL`로 종료된다. 컨테이너 내부에서 `polars`를 제거하고 같은 버전인 `polars-lts-cpu==1.30.0`을 설치했다. Mage 코드와 UI 및 원본 이미지 자체는 변경하지 않았으며, 의존성 교체는 컨테이너의 쓰기 계층에만 적용된다.

최초 생성 명령:

```bash
podman run -d --name mage-original-0979 --init \
  -p 127.0.0.1:3100:6789 -p 172.16.0.134:3100:6789 \
  -v mage-original-0979_data:/var/lib/mage \
  -e USER_CODE_PATH=/var/lib/mage/project \
  -e MAGE_DATA_DIR=/var/lib/mage/data \
  -e MAGE_DATABASE_CONNECTION_URL=sqlite:////var/lib/mage/orchestration.db \
  --entrypoint /bin/sh docker.io/mageai/mageai:0.9.79 -c \
  'if ! python -c "import importlib.metadata as m; assert m.version(\"polars-lts-cpu\") == \"1.30.0\"" >/dev/null 2>&1; then python -m pip uninstall -y polars && python -m pip install --no-deps polars-lts-cpu==1.30.0 || exit 1; fi; exec /app/run_app.sh'
```

호스트에서 루프백 및 사내 IP의 3100 포트 모두 HTTP 200 응답을 확인했다. 다른 PC에서의 실제 접속은 별도 확인이 필요하다.

재시작·중지:

```bash
podman start mage-original-0979
podman stop mage-original-0979
podman logs --tail 50 mage-original-0979
```

이 컨테이너는 원본 비교용이므로 리팩터링한 외부 통신 제거 기능은 적용되지 않는다. 기존 개발 프로젝트 및 사내 서비스 자격증명을 공유하지 않는다.
