# Використовуємо офіційний легкий образ Python
FROM python:3.9-slim

# Встановлюємо робочу директорію всередині контейнера
WORKDIR /app

# Встановлюємо системні залежності (потрібні для роботи з PDF та іншими форматами)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо файл з залежностями
COPY requirements.txt .

# Встановлюємо Python бібліотеки
# --no-cache-dir зменшує розмір образу
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код проєкту в контейнер
COPY . .

# Створюємо папку для даних, якщо її немає
RUN mkdir -p data

# Відкриваємо порти (5000 для API, 8501 для Streamlit)
EXPOSE 5000
EXPOSE 8501

# Команда запуску за замовчуванням (буде перевизначена в docker-compose)
CMD ["python", "api.py"]