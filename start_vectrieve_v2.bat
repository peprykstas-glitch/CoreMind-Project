@echo off
TITLE Vectrieve Launcher v3.1 (Safe Mode) 🛡️
chcp 65001 >nul
cls

echo ===================================================
echo   🛡️ STARTING VECTRIEVE (SAFE MODE)
echo ===================================================

:: 1. CLEANUP
echo [1/5] 🧹 Killing zombies...
taskkill /F /IM node.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
:: Не вбиваємо Docker, хай живе, якщо вже запущений

:: 2. DATABASE
echo [2/5] 🗄️  Starting Database...
docker-compose up -d

echo.
echo ⏳ WAITING 15 SECONDS for Qdrant to wake up...
echo    (Seriously, let it load, or Python will freeze)
:: 👇 ЗБІЛЬШЕНИЙ ТАЙМЕР
timeout /t 15 /nobreak >nul

:: 3. BACKEND
echo [3/5] 🧠 Starting Backend...
:: Додаємо --reload, щоб бачити логи краще
start "Vectrieve BRAIN" cmd /k "call venv\Scripts\activate && python backend\main.py"

:: Чекаємо ще 5 секунд, щоб бекенд завантажив бібліотеки
timeout /t 5 /nobreak >nul

:: 4. FRONTEND
echo [4/5] 💎 Starting Frontend...
start "Vectrieve FACE" cmd /k "cd vectrieve-ui && npm run dev"

:: 5. BROWSER
echo [5/5] 🌐 Launching Browser...
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo.
echo ✅ DONE. If it hangs, check Docker RAM usage.
pause