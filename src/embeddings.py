from __future__ import annotations
import hashlib
import math
import os
LOCAL_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"

class MockEmbedder:
    """Deterministic embedding backend dùng cho testing."""
    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self._backend_name = "mock embeddings fallback"

    def __call__(self, text: str) -> list[float]:
        digest = hashlib.md5(text.encode()).hexdigest()
        seed = int(digest, 16)
        vector = []
        for _ in range(self.dim):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            vector.append((seed / 0xFFFFFFFF) * 2 - 1)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

class LocalEmbedder:
    """Sentence Transformers-backed local embedder (Chạy offline)."""
    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL) -> None:
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name
        self._backend_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return [float(value) for value in embedding]

class OpenAIEmbedder:
    """OpenAI embeddings API-backed embedder."""
    def __init__(self, model_name: str = OPENAI_EMBEDDING_MODEL, api_key: str | None = None) -> None:
        import openai
        self.model_name = model_name
        self._backend_name = model_name
        
        selected_key = api_key or os.getenv("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")
        if not selected_key:
            raise ValueError("OpenAIEmbedder: OPENAI_API_KEY không tồn tại.")

        self.client = openai.OpenAI(api_key=selected_key)

    def __call__(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model_name, input=text)
        return [float(value) for value in response.data[0].embedding]

_mock_embed = MockEmbedder()