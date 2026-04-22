from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import styles, rewrite, training, authors

app = FastAPI(title="NanoChat 风格改写系统", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(styles.router)
app.include_router(rewrite.router)
app.include_router(training.router)
app.include_router(authors.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "NanoChat 风格改写系统运行正常"}


@app.get("/")
async def root():
    return {"message": "欢迎使用 NanoChat 风格改写系统", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_settings
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)