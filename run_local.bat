@echo off
title FaceVault - Neural Intelligence Platform
echo ===================================================
echo   FACEVAULT SENTINEL PLATFORM - LOCAL SERVER
echo ===================================================
echo.
echo Access URL:     http://localhost:8000
echo.
echo Default Credentials:
echo   - Super Admin : superadmin / admin123
echo   - Operator    : operator   / operator123
echo.
echo Starting FastAPI & Face Engine...
echo Press Ctrl+C to stop the server.
echo.
python main.py
pause
