import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    PROJECT_NAME = "Vectrieve AI"
    VERSION = "1.0.0"


    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    if not GROQ_API_KEY:
        raise ValueError("❌ ПОМИЛКА: Не знайдено GROQ_API_KEY у файлі .env!")


    QDRANT_HOST = "localhost"
    QDRANT_PORT = 6333
    COLLECTION_NAME = "Vectrieve_knowledge"
    MODEL_NAME = "llama-3.3-70b-versatile"


settings = Config()