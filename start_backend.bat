@echo off
chcp 65001 >nul
echo ========================================
echo   面试突破助手 - 后端服务
echo ========================================
echo.

cd /d "%~dp0"

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到 Python
    pause
    exit /b 1
)

:: 创建虚拟环境（如果不存在）
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

:: 激活虚拟环境
echo 📦 激活虚拟环境...
call venv\Scripts\activate.bat

:: 安装依赖
echo 📦 安装依赖...
pip install -r backend\requirements.txt -q

:: 创建数据目录
if not exist "data" mkdir data

:: 启动服务
echo.
echo 🚀 启动后端服务...
echo 📡 API地址: http://localhost:8000
echo 📚 Swagger文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
