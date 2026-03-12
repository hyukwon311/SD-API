import logging
import os
from typing import List, Any

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel, Field

from config.settings import ALLOWED_EXTENSIONS
from services.diarization_service import diar_service
from utils.file_handler import save_upload_file, delete_file

# 라우터 설정
router = APIRouter(prefix="/api/v1", tags=["Audio Processing"])
logger = logging.getLogger(__name__)


# 성공 응답 스키마
class DiarizationResponse(BaseModel):
    filename: str = Field(..., example="test_audio.wav")
    status: str = Field(..., example="success")
    segments: List[str] = Field(
        ...,
        example=[
            "0.400 2.880 speaker_0",
            "3.200 5.190 speaker_1"
        ]
    )

class BatchDiarizationResponse(BaseModel):
    status: str = Field(..., example="success")
    results: List[DiarizationResponse]


# 에러 응답 스키마
class ErrorResponse(BaseModel):
    detail: str = Field(..., example="지원하지 않는 오디오 형식입니다.")

class ValidationErrorItem(BaseModel):
    loc: List[Any] = Field(..., example=["body", "file"])
    msg: str = Field(..., example="Field required")
    type: str = Field(..., example="missing")

class ValidationErrorResponse(BaseModel):
    detail: List[ValidationErrorItem]


def _validate_upload_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 없는 업로드는 허용되지 않습니다."
        )

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 오디오 형식입니다: {file.filename}"
        )

def _save_and_validate_file(file: UploadFile) -> str:
    file_path = save_upload_file(file)

    if os.path.getsize(file_path) == 0:
        delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"빈 오디오 파일은 처리할 수 없습니다: {file.filename}"
        )

    return file_path

def _build_result(filename: str, segments: List[str]) -> DiarizationResponse:
    return DiarizationResponse(
        filename=filename,
        status="success",
        segments=segments
    )

def _process_uploaded_files(files: List[UploadFile]) -> List[DiarizationResponse]:
    file_paths: List[str] = []
    original_filenames: List[str] = []

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="업로드된 파일이 없습니다."
        )

    try:
        for file in files:
            _validate_upload_file(file)
            file_path = _save_and_validate_file(file)

            file_paths.append(file_path)
            original_filenames.append(file.filename)

        if len(file_paths) == 1:
            segments = diar_service.process(file_paths[0])
            return [_build_result(original_filenames[0], segments)]

        batch_segments = diar_service.process_many(file_paths)

        return [
            _build_result(filename, segments)
            for filename, segments in zip(original_filenames, batch_segments)
        ]

    except HTTPException:
        raise

    except Exception:
        logger.exception("화자 분리 처리 중 내부 오류 발생")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="화자 분리 처리 중 내부 오류가 발생했습니다."
        )

    finally:
        for file_path in file_paths:
            try:
                delete_file(file_path)
            except Exception:
                logger.exception("임시 파일 삭제 실패: %s", file_path)


@router.post(
    "/diarization",
    summary="Perform Speaker Diarization",
    description="""
    업로드한 오디오 파일에 대해 화자 분리를 수행합니다.

    ### 검증 항목
    - 파일명 존재 여부
    - 허용 확장자 여부
    - 0바이트 빈 파일 여부

    ### 요청 형식
    - Content-Type: multipart/form-data
    - form-data field: `file`

    ### cURL 예시
    ```bash
    curl -X POST "http://localhost:9600/api/v1/diarization" \
        -F "file=@./sample.wav"
    ```

    ### 처리 흐름
    1. 업로드 파일을 임시 디렉토리에 저장
    2. NeMo Sortformer 모델로 화자 분리 수행
    3. 결과 반환
    4. 임시 파일 삭제
    """,
    response_model=DiarizationResponse,
    responses={
        200: {
            "description": "화자 분리 성공",
            "content": {
                "application/json": {
                    "example": {
                        "filename": "test_audio.wav",
                        "status": "success",
                        "segments": [
                            "0.400 2.880 speaker_0",
                            "3.200 5.190 speaker_1"
                        ]
                    }
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "잘못된 요청",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_filename": {
                            "summary": "파일명 없음",
                            "value": {
                                "detail": "파일명이 없는 업로드는 허용되지 않습니다."
                            }
                        },
                        "unsupported_format": {
                            "summary": "지원하지 않는 확장자",
                            "value": {
                                "detail": "지원하지 않는 오디오 형식입니다: sample.txt"
                            }
                        },
                        "empty_audio": {
                            "summary": "빈 오디오 파일",
                            "value": {
                                "detail": "빈 오디오 파일은 처리할 수 없습니다."
                            }
                        }
                    }
                }
            }
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "요청 형식 검증 실패",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "file"],
                                "msg": "Field required",
                                "type": "missing"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "model": ErrorResponse,
            "description": "서버 내부 오류",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "화자 분리 처리 중 내부 오류가 발생했습니다."
                    }
                }
            }
        }
    }
)
async def process_diarization(
    file: UploadFile = File(..., description="화자 분리를 수행할 오디오 파일")
):
    results = _process_uploaded_files([file])
    return results[0]


@router.post(
    "/diarization/batch",
    summary="Perform batch speaker diarization",
    description="""
    여러 개의 오디오 파일에 대해 화자 분리를 수행합니다.

    ### 검증 항목
    - 업로드 파일 존재 여부
    - 파일명 존재 여부
    - 허용 확장자 여부
    - 0바이트 빈 파일 여부

    ### 요청 형식
    - Content-Type: multipart/form-data
    - form-data field: `files`
    - 같은 키 `files`로 여러 파일 업로드

    ### cURL 예시
    ```bash
    curl -X POST "http://localhost:9600/api/v1/diarization/batch" \
        -F "files=@./audio1.wav" \
        -F "files=@./audio2.wav"
    ```
    """,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["files"],
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "format": "binary"
                                },
                                "description": "화자 분리를 수행할 오디오 파일들"
                            }
                        }
                    }
                }
            }
        }
    },
    response_model=BatchDiarizationResponse,
    responses={
        200: {
            "description": "배치 화자 분리 성공",
            "content": {
                "application/json": {
                    "example": {
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
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "잘못된 요청",
            "content": {
                "application/json": {
                    "examples": {
                        "no_files": {
                            "summary": "파일 없음",
                            "value": {"detail": "업로드된 파일이 없습니다."}
                        },
                        "unsupported_format": {
                            "summary": "지원하지 않는 확장자",
                            "value": {"detail": "지원하지 않는 오디오 형식입니다: sample.txt"}
                        },
                        "empty_audio": {
                            "summary": "빈 파일",
                            "value": {"detail": "빈 오디오 파일은 처리할 수 없습니다: audio1.wav"}
                        }
                    }
                }
            }
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "요청 형식 검증 실패",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "files"],
                                "msg": "Field required",
                                "type": "missing"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "model": ErrorResponse,
            "description": "서버 내부 오류",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "배치 화자 분리 처리 중 내부 오류가 발생했습니다."
                    }
                }
            }
        }
    }
)
async def process_diarization_batch(
    files: list[UploadFile] = File(..., description="화자 분리를 수행할 오디오 파일들")
):
    results = _process_uploaded_files(files)
    return BatchDiarizationResponse(
        status="success",
        results=results
    )