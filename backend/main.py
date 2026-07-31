import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import APP_NAME, APP_VERSION, DEBUG
from .utils.logger import setup_logger
from .database import init_db
from .api.routes import health_router, users_router, interviews_router, positions_router, auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    init_db()
    print(f"[OK] {APP_NAME} v{APP_VERSION} started successfully")
    print(f"[INFO] Swagger docs: http://localhost:8000/docs")
    yield
    print(f"[INFO] {APP_NAME} shutting down")

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="基于 RAG + Multi-Agent 的智能面试模拟系统",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS配置 —— 开发环境允许多个前端端口，生产环境应收窄为实际域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3003",   # Express 前端
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:3003",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件 —— 记录每个请求的方法/路径/耗时/状态码
request_logger = setup_logger(name="request")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    request_logger.info(
        f'{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)'
    )
    return response

# 注册路由
app.include_router(health_router)
app.include_router(users_router)
app.include_router(interviews_router)
app.include_router(positions_router)
app.include_router(auth_router)

@app.get("/")
async def root():
    return {
        "message": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=DEBUG)
