from __future__ import annotations
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import openai

# --- GIAI ĐOẠN 1: NẠP CẤU HÌNH BIẾN MÔI TRƯỜNG ---
load_dotenv(override=True)
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    print("[-] Lỗi: OPENAI_API_KEY không tồn tại trong file .env")
    sys.exit(1)

# Khởi tạo client dùng chung cho các hàm bổ trợ
client = openai.OpenAI(api_key=API_KEY)

# --- IMPORT MODULES SAU KHI CÓ CẤU HÌNH ---
from src.chunking import AgenticChunker
from src.agent import KnowledgeBaseAgent
from src.embeddings import OpenAIEmbedder
from src.models import Document
from src.store import EmbeddingStore

# --- DANH SÁCH 6 CÂU HỎI TÍCH HỢP THEO YÊU CẦU ---
INTEGRATED_QUERIES = [
    "Câu 1: Bộ luật Lao động năm 2019 (Luật số 45/2019/QH14) chính thức có hiệu lực thi hành kể từ ngày tháng năm nào?",
    "Câu 2: Theo Bộ luật Lao động 2019, hợp đồng lao động được phân loại thành mấy loại chính? Đó là những loại nào?",
    "Câu 3: Quy định pháp luật không cho phép áp dụng thời gian thử việc đối với trường hợp người lao động giao kết loại hợp đồng lao động nào?",
    "Câu 4: Theo quy định, thời gian thử việc tối đa đối với công việc của người quản lý doanh nghiệp (theo quy định của Luật Doanh nghiệp, Luật Quản lý, sử dụng vốn nhà nước đầu tư vào sản xuất, kinh doanh tại doanh nghiệp) là bao nhiêu ngày?",
    "Câu 5: Trong dịp lễ Quốc khánh 02/9, người lao động được nghỉ làm việc và hưởng nguyên lương tổng cộng bao nhiêu ngày?",
    "Câu 6: Lộ trình điều chỉnh tuổi nghỉ hưu đối với người lao động làm việc trong điều kiện lao động bình thường được thực hiện cho đến khi đạt mức độ tuổi nào đối với nam và nữ?"
]

SAMPLE_FILES = ["data/luat_lao_dong.md"]

def chunking_llm_fn(prompt: str) -> str:
    """Hàm gọi LLM phục vụ cho AgenticChunker và KnowledgeBaseAgent."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def load_documents_from_files(file_paths: list[str]) -> list[Document]:
    """Tải và đóng gói tài liệu từ file hệ thống."""
    documents: list[Document] = []
    for raw_path in file_paths:
        path = Path(raw_path)
        if not path.exists():
            print(f"[!] Cảnh báo: File {raw_path} không tồn tại.")
            continue
        content = path.read_text(encoding="utf-8")
        documents.append(Document(id=path.stem, content=content, metadata={"source": str(path)}))
    return documents

def run_manual_demo(use_integrated: bool = False) -> int:
    # 1. Load tài liệu
    raw_docs = load_documents_from_files(SAMPLE_FILES)
    if not raw_docs: return 1

    # 2. Xử lý cắt nhỏ văn bản (Chunking)
    agentic_chunker = AgenticChunker(llm_fn=chunking_llm_fn, max_chunk_size=1000)
    chunked_docs = []
    
    print("\n=== [GIAI ĐOẠN 1] Agentic Chunking ===")
    for doc in raw_docs:
        print(f"  > Đang xử lý: {doc.id}")
        chunks = agentic_chunker.chunk(doc.content)
        for i, text in enumerate(chunks):
            chunked_docs.append(Document(id=f"{doc.id}_{i}", content=text, metadata=doc.metadata))

    # 3. Khởi tạo Embedder và Store (Truyền API_KEY tường minh)
    embedder = OpenAIEmbedder(api_key=API_KEY)
    store = EmbeddingStore(collection_name="hust_labor_law", embedding_fn=embedder)
    store.add_documents(chunked_docs)

    # 4. Khởi tạo Agent
    agent = KnowledgeBaseAgent(store=store, llm_fn=chunking_llm_fn)

# 5. Thực thi truy vấn và liệt kê chi tiết phục vụ báo cáo
    queries = INTEGRATED_QUERIES if use_integrated else []
    
    print(f"\n{'='*30} DỮ LIỆU CHI TIẾT {'='*30}")
    print(f"Tổng số chunks trong hệ thống: {len(chunked_docs)}")

    for idx, q in enumerate(queries, 1):
        print(f"\nQUERY #{idx}: {q}")
        
        results = store.search(q, top_k=5)
        
        print(f"--- Top-5 Retrieved Chunks ---")
        for rank, res in enumerate(results, 1):
            content_preview = res['content'].strip().replace('\n', ' ')
            summary = content_preview[:150] + "..." if len(content_preview) > 150 else content_preview
            is_relevant = "Yes" if res['score'] > 0.5 else "No"
            
            print(f"  [{rank}] Score: {res['score']:.4f} | Relevant: {is_relevant}")
            print(f"      Content Summary: {summary}")
        
        # Lấy câu trả lời từ Agent
        ans = agent.answer(q, top_k=5)
        print(f"--- Agent Answer (Brief) ---")
        print(f"  {ans[:250]}...") 

    return 0

def main() -> int:
    is_auto = len(sys.argv) > 1 and sys.argv[1].lower() == "auto"
    return run_manual_demo(use_integrated=is_auto)

if __name__ == "__main__":
    sys.exit(main())