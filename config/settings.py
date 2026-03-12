import os

# 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, "data", "temp_audio")

# AI 모델 설정
MODEL_NAME = "nvidia/diar_streaming_sortformer_4spk-v2.1"

# 허용 오디오 확장자
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac"}
