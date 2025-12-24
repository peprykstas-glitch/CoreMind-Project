@echo off
TITLE Vectrieve Launcher 🚀
chcp 65001 >nul

echo ===================================================
echo   STARTING Vectrieve SYSTEM
echo ===================================================

:: 1. Запускаємо Qdrant (База даних)
echo [1/4] Launching Database...
docker-compose up -d

:: Чекаємо 5 секунд, поки база прокинеться
timeout /t 5 /nobreak >nul

:: 2. Запускаємо Backend
echo [2/4] Starting Backend...
:: start "" запускає в новому вікні
start "Vectrieve Backend" cmd /k "python backend/main.py"

:: 3. Запускаємо Frontend
echo [3/4] Starting Frontend...
start "Vectrieve Frontend" cmd /k "streamlit run frontend/main.py"

:: 4. Запускаємо Ngrok (для доступу з інтернету)
echo [4/4] Opening Ngrok Tunnel...
start "Ngrok Tunnel" cmd /k "ngrok http 8501"

echo.
echo ===================================================
echo   SYSTEM ONLINE! 🟢
echo   Minimise the black windows, do not close them.
echo ===================================================
pause