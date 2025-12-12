from openai import OpenAI

# Спробуємо обидва варіанти адреси
hosts_to_test = [
    "http://localhost:11434/v1",
    "http://127.0.0.1:11434/v1"
]

print("🔍 Починаю діагностику Ollama...\n")

for host in hosts_to_test:
    print(f"👉 Перевіряю адресу: {host}")
    client = OpenAI(base_url=host, api_key="ollama")
    
    try:
        # 1. Перевіряємо список моделей
        models = client.models.list()
        print(f"✅ Зв'язок Є! Знайдено моделей: {len(models.data)}")
        
        # Виводимо імена моделей
        available_models = [m.id for m in models.data]
        print(f"   Список моделей: {available_models}")
        
        # 2. Перевіряємо генерацію (тест розуму)
        print("   Спроба генерації...")
        response = client.chat.completions.create(
            model="llama3.2:3b", # Переконайся, що ім'я моделі тут таке ж, як у списку вище
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(f"✅ Відповідь отримана: {response.choices[0].message.content}\n")
        
    except Exception as e:
        print(f"❌ ПОМИЛКА підключення до {host}:")
        print(f"   {str(e)}\n")

print("🏁 Діагностику завершено.")