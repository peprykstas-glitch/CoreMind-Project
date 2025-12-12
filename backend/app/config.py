import os
# from dotenv import load_dotenv # Вимикаємо це, щоб уникнути плутанини

# load_dotenv()

class Settings:
    PROJECT_NAME: str = "CoreMind API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # --- LLM SETTINGS ---
    # ЖОРСТКЕ НАЛАШТУВАННЯ (HARDCODED)
    # Ми прибрали os.getenv, щоб точно взяти правильну адресу
    OLLAMA_HOST: str = "http://127.0.0.1:11434/v1"
    
    # Назва моделі
    OLLAMA_MODEL: str = "llama3.2:3b" 
    
    # --- VECTOR DB SETTINGS ---
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    COLLECTION_NAME: str = "coremind_knowledge"

settings = Settings()