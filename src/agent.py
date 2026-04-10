from __future__ import annotations
from typing import Callable
from .store import EmbeddingStore

class KnowledgeBaseAgent:
    def __init__(self, store, llm_fn):
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, query: str, top_k: int = 5) -> str:
        results = self.store.search(query, top_k=top_k)
        context = "\n".join([r['content'] for r in results])
        prompt = f"""
Nhiệm vụ: Trả lời câu hỏi dựa trên ngữ cảnh pháp luật được cung cấp.
Yêu cầu:
1. Trả lời trực tiếp, không sử dụng câu dẫn (ví dụ: "Dựa trên ngữ cảnh...", "Theo quy định...").
2. Ngôn ngữ chính xác, học thuật, không biểu thị cảm xúc.
3. Nếu ngữ cảnh có thông tin, hãy trích dẫn số Điều cụ thể.
4. Nếu ngữ cảnh không đủ thông tin, chỉ trả lời: "Thông tin không có trong tài liệu."

Ngữ cảnh:
{context}

Câu hỏi: {query}
Trả lời:"""

        response = self.llm_fn(prompt)
        return response.strip()