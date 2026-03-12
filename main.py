import logging
from fastapi import FastAPI
from pydantic import BaseModel, Field
from routers import diarization

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)

class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")

app = FastAPI(
    title="Speaker Diarization API",
    description="""
NeMo Sortformer 기반 화자 분리 API

### Endpoints
- `GET /health` : 서버 상태 확인
- `POST /api/v1/diarization` : 오디오 업로드 후 화자 분리 수행

### Docs
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`
""",
    version="1.0.0"
)

@app.get(
    "/health", 
    tags=["System"],
    summary="Health check",
    description="서버가 정상적으로 실행 중인지 확인합니다.",
    response_model=HealthResponse,
    responses={
        200: {
            "description": "서버 정상 상태",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy"
                    }
                }
            }
        }
    }
)
def health_check():
    return {"status": "healthy"}

# 라우터 등록 
app.include_router(diarization.router)