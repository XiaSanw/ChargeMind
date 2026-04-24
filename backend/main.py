"""
ChargeMind Demo — FastAPI 入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from api.diagnosis import router as diagnosis_router

app = FastAPI(
    title="ChargeMind Demo",
    description="充电场站诊断平台 — 黑客松演示版",
    version="0.1.0-demo",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnosis_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0-demo"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
