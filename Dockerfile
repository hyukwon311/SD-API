# 베이스 이미지: NVIDIA GPU 가속을 위해 CUDA 12.4 환경 사용
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

LABEL description="Speaker Diarization API - Production Image"

# 환경 변수: 파이썬 출력 최적화 및 타임존 설정
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Seoul \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

# 필수 시스템 패키지 설치 (오디오 처리를 위한 ffmpeg, libsndfile 등 포함)
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    ca-certificates \
    curl \
    ffmpeg \
    sox \
    libsndfile1 \
    git && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-dev \
    python3.10-venv \
    python3-pip && \
    ln -sf /usr/bin/python3.10 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.10 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

ARG UID=1000
ARG GID=1000

RUN groupadd -g ${GID} appuser && \
    useradd -m -u ${UID} -g ${GID} -s /bin/bash appuser

WORKDIR /app
    
COPY requirements.txt /app/requirements.txt

RUN python3 -m pip install --upgrade pip && \
    pip install numpy Cython packaging typing_extensions && \
    pip install -r /app/requirements.txt


# 소스 코드 복사 
COPY . /app

# 데이터 및 로그 폴더 생성 및 권한 설정
RUN mkdir -p /app/data/temp_audio /app/outputs /app/logs && \
    chown -R appuser:appuser /app

# 비루트 사용자로 전환
USER appuser

EXPOSE 9100

CMD ["python", "run_server.py"]