# 🎙️ Speaker Diarization API

NeMo Sortformer 모델 기반의 화자 분리(Speaker Diarization) REST API 서버입니다.  
오디오 파일을 업로드하면 각 구간별 화자를 자동으로 분리하여 반환합니다.

---

## 📋 목차

- [개요](#개요)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [시작하기](#시작하기)
- [API 명세](#api-명세)
- [설정](#설정)
- [로깅 및 헬스체크](#로깅-및-헬스체크)

---

## 개요

이 서비스는 NVIDIA NeMo의 **Sortformer** 모델(`nvidia/diar_streaming_sortformer_4spk-v2.1`)을 사용하여 오디오 파일에서 화자를 분리합니다. 단일 파일 및 배치(다중 파일) 처리를 모두 지원하며, FastAPI 기반의 REST API로 제공됩니다.

**주요 기능**

- 단일 오디오 파일 화자 분리
- 다중 오디오 파일 배치 화자 분리
- Docker + NVIDIA GPU 가속 지원
- Swagger UI / ReDoc 자동 문서 제공

---

## 기술 스택

| 항목 | 내용 |
|------|------|
| Language | Python 3.10 |
| Framework | FastAPI |
| AI Model | NVIDIA NeMo Sortformer (`nvidia/diar_streaming_sortformer_4spk-v2.1`) |
| GPU | CUDA 12.4 |
| Container | Docker, Docker Compose |
| Server | Uvicorn |

---

## 프로젝트 구조

```
.
├── main.py                  # FastAPI 앱 진입점, 헬스체크 엔드포인트
├── run_server.py            # Uvicorn 서버 실행 스크립트
├── requirements.txt         # Python 패키지 의존성
├── Dockerfile               # Docker 이미지 빌드 설정
├── docker-compose.yml       # Docker Compose 서비스 설정
├── config/
│   └── settings.py          # 경로, 모델명, 허용 확장자 설정
├── routers/
│   └── diarization.py       # API 라우터 및 요청/응답 스키마
├── services/
│   └── diarization_service.py  # NeMo 모델 로드 및 추론 로직
├── utils/
│   └── file_handler.py      # 업로드 파일 저장/삭제 유틸리티
└── data/
    └── temp_audio/          # 임시 파일 저장 디렉토리
```

---

## 시작하기

### 사전 요구사항

- Docker & Docker Compose
- NVIDIA GPU 및 드라이버
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

### 1. 저장소 클론

```bash
git clone https://github.com/hyukwon311/SD-API.git
cd SD-API
```

### 2. Docker Compose로 실행

```bash
docker compose up -d --build
```

서버가 정상적으로 시작되면 `http://localhost:9600` 에서 API를 사용할 수 있습니다.

> **참고:** 최초 실행 시 NeMo 모델 다운로드로 인해 시작에 수 분이 소요될 수 있습니다.

### 3. 동작 확인

```bash
curl http://localhost:9600/health
# {"status": "healthy"}
```

---

## API 명세

### Base URL

```
http://localhost:9600
```

### 인터랙티브 문서

| 문서 | URL |
|------|-----|
| Swagger UI | `http://localhost:9600/docs` |
| ReDoc | `http://localhost:9600/redoc` |
| OpenAPI JSON | `http://localhost:9600/openapi.json` |

---

### `GET /health`

서버 상태를 확인합니다.

**응답 예시**

```json
{
  "status": "healthy"
}
```

---

### `POST /api/v1/diarization`

단일 오디오 파일에 대해 화자 분리를 수행합니다.

**요청**

| 항목 | 내용 |
|------|------|
| Content-Type | `multipart/form-data` |
| Field | `file` |
| 허용 형식 | `.wav`, `.mp3`, `.m4a`, `.flac` |

**cURL 예시**

```bash
curl -X POST "http://localhost:9600/api/v1/diarization" \
     -F "file=@./sample.wav"
```

**성공 응답 (200)**

```json
{
  "filename": "sample.wav",
  "status": "success",
  "segments": [
    "0.400 2.880 speaker_0",
    "3.200 5.190 speaker_1"
  ]
}
```

> 각 segment는 `시작시간(초) 종료시간(초) 화자ID` 형식입니다.

**에러 응답**

| 코드 | 설명 |
|------|------|
| 400 | 파일명 없음 / 미지원 확장자 / 빈 파일 |
| 422 | 요청 형식 오류 (파일 누락 등) |
| 500 | 서버 내부 오류 |

---

### `POST /api/v1/diarization/batch`

여러 오디오 파일에 대해 배치 화자 분리를 수행합니다.

**요청**

| 항목 | 내용 |
|------|------|
| Content-Type | `multipart/form-data` |
| Field | `files` (동일 키로 여러 파일 업로드) |
| 허용 형식 | `.wav`, `.mp3`, `.m4a`, `.flac` |

**cURL 예시**

```bash
curl -X POST "http://localhost:9600/api/v1/diarization/batch" \
     -F "files=@./audio1.wav" \
     -F "files=@./audio2.wav"
```

**성공 응답 (200)**

```json
{
  "status": "success",
  "results": [
    {
      "filename": "audio1.wav",
      "status": "success",
      "segments": [
        "0.400 2.880 speaker_0",
        "3.200 5.190 speaker_1"
      ]
    },
    {
      "filename": "audio2.wav",
      "status": "success",
      "segments": [
        "1.100 2.700 speaker_0",
        "3.000 4.500 speaker_1"
      ]
    }
  ]
}
```

---

## 설정

`config/settings.py`에서 주요 설정값을 변경할 수 있습니다.

```python
# 임시 파일 저장 경로
TEMP_DIR = os.path.join(BASE_DIR, "data", "temp_audio")

# 사용할 NeMo 모델
MODEL_NAME = "nvidia/diar_streaming_sortformer_4spk-v2.1"

# 허용 오디오 확장자
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac"}
```

### Docker Compose 리소스 설정

`docker-compose.yml`에서 메모리 및 GPU 설정을 변경할 수 있습니다.

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
    limits:
      memory: 8G
```

### 포트 설정

기본 포트는 외부 `9600` → 내부 `9100`으로 매핑됩니다. 변경이 필요하면 `docker-compose.yml`의 `ports` 항목을 수정하세요.

### 볼륨

컨테이너 재시작 시에도 데이터가 유지되도록 Named Volume을 사용합니다.

| 볼륨 이름 | 컨테이너 경로 | 용도 |
|-----------|--------------|------|
| `diarization-data` | `/app/data` | 임시 오디오 파일 저장 |
| `diarization-logs` | `/app/logs` | 애플리케이션 로그 저장 |

---

## 로깅 및 헬스체크

### 로그

애플리케이션 로그는 콘솔과 파일에 동시에 출력됩니다.

- **콘솔:** Docker 로그에서 실시간 확인 (`docker compose logs -f`)
- **파일:** `/app/logs/app.log` (컨테이너 내부 / `diarization-logs` 볼륨에 저장)
- **Docker 로그 드라이버:** `json-file`, 최대 10MB × 3개 파일 유지

### 헬스체크

컨테이너는 30초마다 `/health` 엔드포인트를 호출하여 상태를 확인합니다.

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:9100/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```