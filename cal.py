import math
import os
from src.embeddings import OpenAIEmbedder
from src.chunking import compute_similarity

def run_similarity_test():
    # Khởi tạo API Key trực tiếp để bypass lỗi .env
    api_key = "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"
    
    # Khởi tạo embedder với API Key
    try:
        embedder = OpenAIEmbedder(api_key=api_key)
    except Exception as e:
        print(f"Lỗi khởi tạo: {e}")
        return

    # Danh sách các cặp câu thử nghiệm
    pairs = [
        {"id": 1, "a": "xe ô tô điện hiện đại phong cách", "b": "xe vinfast", "pred": "High"},
        {"id": 2, "a": "Người lao động có quyền đơn phương chấm dứt HĐLĐ.", "b": "Nhân viên có thể chủ động xin nghỉ việc.", "pred": "High"},
        {"id": 3, "a": "Hợp đồng lao động phải được lập thành văn bản.", "b": "Thành phố Hà Nội là thủ đô của Việt Nam.", "pred": "Low"},
        {"id": 4, "a": "Thử việc không quá 180 ngày.", "b": "Thời gian thử việc tối đa của người quản lý là 6 tháng.", "pred": "High"},
        {"id": 5, "a": "Lương tháng 13 là bắt buộc.", "b": "Thưởng tết không phải là khoản chi cứng.", "pred": "High"},
    ]

    print(f"\n| Pair | Dự đoán | Actual Score | Đúng? |")
    print(f"| :--- | :--- | :--- | :--- |")

    for p in pairs:
        vec_a = embedder(p["a"])
        vec_b = embedder(p["b"])
        score = compute_similarity(vec_a, vec_b)
        
        # Xác định đúng/sai (Ngưỡng High > 0.3)
        is_correct = "Yes" if (score > 0.3 and p["pred"] == "High") or (score <= 0.3 and p["pred"] == "Low") else "No"
        print(f"| {p['id']} | {p['pred']} | {score:.4f} | {is_correct} |")

if __name__ == "__main__":
    run_similarity_test()