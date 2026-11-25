@echo off
title IAMD Chat
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Creando entorno virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: no se pudo crear el venv. Asegurate de tener Python instalado.
        pause
        exit /b 1
    )
    echo Instalando dependencias...
    call .venv\Scripts\activate.bat
    pip install flask flask-socketio python-socketio
) else (
    call .venv\Scripts\activate.bat
)

echo.
echo ============================================================
echo   IAMD CHAT — Iniciando servidor
echo   Abre http://localhost:5000 en tu navegador
echo   Pulsa Ctrl+C para parar
echo ============================================================
echo.

python app.py
pause