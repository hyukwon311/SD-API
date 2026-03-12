import os
import shutil
import uuid
from fastapi import UploadFile
from config.settings import TEMP_DIR

def save_upload_file(upload_file: UploadFile) -> str:
    """업로드된 파일을 지정된 임시 폴더에 UUID 기반 파일명으로 저장"""
    os.makedirs(TEMP_DIR, exist_ok=True)

    ext = os.path.splitext(upload_file.filename)[1]
    saved_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(TEMP_DIR, saved_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return file_path

def delete_file(file_path: str):
    """분석이 끝난 임시 파일을 삭제"""
    if os.path.exists(file_path):
        os.remove(file_path)