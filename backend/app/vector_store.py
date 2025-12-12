from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from fastembed import TextEmbedding
from app.config import settings
import uuid
import time

class VectorStore:
    def __init__(self):
        print("Connecting to Qdrant...")
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.collection_name = settings.COLLECTION_NAME
        
        print("Loading Embedding Model (this might take a moment on first run)...")
        # Використовуємо легку і швидку модель 'bge-small-en-v1.5' (або мультимовну)
        # Вона автоматично завантажиться при першому запуску
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        try:
            self.client.get_collection(self.collection_name)
        except (UnexpectedResponse, Exception):
            print(f"Creating collection '{self.collection_name}'...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=384, # Розмір векторів для моделі bge-small
                    distance=models.Distance.COSINE
                )
            )

    def add_document(self, text: str, meta: dict = None):
        """Перетворює текст на вектор і зберігає в Qdrant"""
        doc_id = str(uuid.uuid4())
        
        # 1. Генерація реального вектора
        # fastembed повертає генератор, тому беремо перший елемент
        vector = list(self.embedding_model.embed([text]))[0]

        payload = {"content": text}
        if meta:
            payload.update(meta)

        # 2. Запис у базу
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=doc_id,
                    vector=vector.tolist(),
                    payload=payload
                )
            ]
        )
        print(f"Document {doc_id} indexed.")
        return doc_id

    def search(self, query: str, limit: int = 3):
        """Шукає схожі документи за текстом запиту"""
        # 1. Векторизуємо запит
        query_vector = list(self.embedding_model.embed([query]))[0]

        # 2. Шукаємо в Qdrant
        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=limit
        )
        return hits

# Ініціалізація
vector_db = VectorStore()