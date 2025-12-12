@echo off
ECHO Starting CoreMind v0.4 (Ollama Edition)...

REM --- Запускаємо "Кухню" (api.py) у новому вікні ---
ECHO Starting Backend API (api.py)...
start "CoreMind API" cmd /k ".\venv\Scripts\activate.bat && python api.py"

REM --- Чекаємо, поки порт 5000 почне слухати ---
ECHO Waiting for API server (port 5000) to be ready...
:checkport
REM Перевіряємо, чи є активне з'єднання на порту 5000
netstat -ano | findstr "LISTENING" | findstr ":5000" > nul
REM Якщо команда findstr знайшла порт (errorlevel 0), йдемо до запуску UI
if %errorlevel% equ 0 goto startui
REM Якщо порт не знайдено, чекаємо 3 секунди і перевіряємо знову
ECHO Port 5000 not ready yet, checking again in 3 seconds...
timeout /t 3 /nobreak > nul
goto checkport

:startui
REM --- Запускаємо "Офіціанта" (app.py) у новому вікні ---
ECHO API is ready! Starting Frontend UI (app.py)...
start "CoreMind UI" cmd /k ".\venv\Scripts\activate.bat && streamlit run app.py"

ECHO Both servers are starting in new windows.