from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, upload, plans,reports, progress
from app.core.database import engine, Base
import app.models  # 必须导入，否则表不会被注册

app = FastAPI(title="SchedWise AI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(plans.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(progress.router, prefix="/api")


@app.on_event("startup")
async def init_db():
    """启动时自动建表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)