# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Phạm Trà My
**Nhóm:** C401_F1
**Ngày:** 10/4/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> *High cosine similarity cho biết hai vector có hướng gần như trùng nhau trong không gian vector đa chiều, thể hiện sự tương đồng cao về ngữ nghĩa giữa hai đoạn văn bản.*

**Ví dụ HIGH similarity:**
- Sentence A: Xe ô tô điện hiện đại, phong cách
- Sentence B: Xe Vinfast
- Tại sao tương đồng: Dù câu A sử dụng các tính từ chung chung và câu B sử dụng một danh từ riêng, nhưng cơ chế nhúng dựa trên ngữ cảnh (như Transformer-based embeddings) có khả năng hiểu được mối liên hệ thực tế giữa thực thể (VinFast) và đặc tính (ô tô điện, phong cách). 

**Ví dụ LOW similarity:**
- Sentence A: Xe ô tô điện hiện đại, phong cách
- Sentence B: Thủ đô Hà Nội thật đẹp
- Tại sao khác: Hai câu thuộc hai phạm trù nội dung hoàn toàn khác biệt, không có sự liên quan về ngữ cảnh hay ý nghĩa thực tế.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> *Cosine similarity tập trung vào hướng (góc giữa hai vector) để đo lường ngữ nghĩa, trong khi Euclidean distance bị ảnh hưởng bởi độ dài (magnitude) của vector; điều này giúp tránh sai số khi so sánh các đoạn văn bản có độ dài khác nhau nhưng nội dung tương đồng.*

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *[(10,000 - 500) / (500 - 50)] = 22.11 chunks*
> *Đáp án: 23 chunks*

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Overlap nhiều hơn giúp duy trì ngữ cảnh liên tục giữa các điểm cắt, đảm bảo thông tin quan trọng nằm ở cuối chunk này không bị mất ý nghĩa khi xuất hiện ở đầu chunk kế tiếp, từ đó cải thiện độ chính xác khi truy vấn (retrieval).*

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Luật Lao động Việt Nam 2019

**Tại sao nhóm chọn domain này?**
> Chọn Luật Lao động Việt Nam 2019 vì đây là một lĩnh vực có nhiều tài liệu pháp lý phức tạp, đòi hỏi sự hiểu biết sâu sắc về ngôn ngữ và cấu trúc văn bản. Domain này cũng có nhiều quy định và điều khoản liên quan đến quyền lợi của người lao động, làm cho việc retrieval thông tin chính xác trở nên rất quan trọng.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | Bộ luật Lao Động Việt Nam 2019| https://datafiles.chinhphu.vn/cpp/files/vbpq/2019/12/45.signed.pdf | 193202 |  |


### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| doc_title | string | "Bộ luật Lao động 2019" | Giúp hệ thống lọc (filter) ngay lập tức nếu người dùng chỉ định rõ "Theo bộ luật lao động 2019...". Tránh nhầm lẫn với bộ luật khác/cũ (2012).|
| doc_id | string | "45/2019/QH14" | Nhiều người dùng (đặc biệt là dân luật/nhân sự) thường tra cứu bằng số hiệu văn bản. Đây là keyword định danh chính xác tuyệt đối. |
| effective_date | date | "01/01/2021" | Giúp hệ thống đánh giá tính thời sự của văn bản hoặc dùng để trả lời các câu hỏi về thời điểm áp dụng luật. |
| Chapter | integer | 1, 2, 3, ... | Giúp gom nhóm ngữ cảnh. Ví dụ: Các chunk thuộc Chương III sẽ có độ ưu tiên cao khi câu hỏi liên quan đến "Hợp đồng lao động".|
| article_number | integer | 10, 20 | Cực kỳ quan trọng. Người dùng thường hỏi trực tiếp "Điều 20 quy định gì?". Metadata này cho phép trích xuất chính xác (exact match) chunk chứa điều luật đó. |
| article_title | string | "Loại hợp đồng lao động" | Bổ sung semantic context. Tên điều thường chứa từ khóa tóm tắt toàn bộ nội dung của điều luật đó.|
| source_url | string |  "https://datafiles.chinhphu.vn/cpp/files/vbpq/2019/12/45.signed.pdf" | Không trực tiếp giúp tìm kiếm, nhưng là metadata bắt buộc để Generator (LLM) đính kèm link trích dẫn (citation) vào câu trả lời cuối cùng, tăng độ tin cậy. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Strategy Của Tôi

**Loại:** [custom strategy (Agent Chunker)]

**Mô tả cách hoạt động:**
> *Sử dụng LLM để phân tích ngữ nghĩa và xác định semantic boundaries trong văn bản thay vì dựa vào các dấu hiệu như độ dài ký tự hay dấu câu. Cụ thể, LLM sẽ nhận nhiệm vụ chèn ký tự phân tách ||| vào các vị trí mà nội dung chuyển giao sang một nội dung hoặc chủ đề mới. Sau khi LLM phân đoạn, nếu đoạn nào vượt quá kích thước max_chunk_size,hệ thống sẽ áp dụng FixedSizeChunker để đảm bảo tính ổn định cho bộ nhớ đệm của vector store.*

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Đối với domain là văn bản pháp luật (Bộ luật Lao động), các quy định thường có cấu trúc phức tạp với nhiều điều, khoản có độ dài ngắn rất khác nhau. Việc sử dụng AgenticChunker giúp đảm bảo toàn vẹn của một quy định, tránh việc một điều luật bị cắt nhỏ từ đó nâng cao độ chính xác khi Agent thực hiện trả lời câu hỏi dựa trên căn cứ luật.*

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Luật lao động Việt Nam | FixedSizeChunker (`fixed_size`) | 1074 | 199.87 | Không |
| Luật lao động Việt Nam | SentenceChunker (`by_sentences`) | 554 | 346.92 | Có |
| Luật lao động Việt Nam | RecursiveChunker (`recursive`) | 1652 | 115.27 | Có 

### So Sánh Với Thành Viên Khác


| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Duy Anh | Custom Strategy (Regex Based Chunking) | 8.5 | Bảo toàn ngữ cảnh tốt | Khi điều luật quá dài, đoạn chunk sinh ra sẽ vượt qua giới hạn context window. Hao phí khi embedding. Sự thừa thãi khi truy xuất.  |
| Lại Gia Khánh | Semantic Chunking | 8 | Giữ nguyên đơn vị nghĩa (câu/điều), cải thiện độ chính xác truy vấn và khả năng trích dẫn nguồn; giảm nhiễu khi trả lời câu hỏi chuyên sâu. | Phụ thuộc vào chất lượng embedding và ngưỡng similarity; cần tinh chỉnh threshold; tốn tài nguyên hơn và có thể tạo chunk kích thước không đồng đều. |
| Mạc Phương Nga | FixedSizeChunker | 10 | Xử lý đơn giản, nhanh. Kiểm soát được lượng token đưa vào LLM | Phụ thuộc nhiều vào chunk_size và overlap, cần kiểm thử nhiều lần để tìm cặp thông số tối ưu. |
| Nguyễn Phạm Trà My | AgenticChunker |10| Bảo tồn trọn vẹn bối cảnh và tính logic của văn bản bằng cách phân đoạn dựa trên ranh giới ngữ nghĩa thay vì cắt theo độ dài vật lý cố định. | Chi phí cao và tốc độ xử lý chậm do phụ thuộc hoàn toàn vào việc gọi API từ LLM cho từng đoạn văn bản.|
| Trương Minh Sơn |Parent–Child |7.8/10|Trả lời câu hỏi, tìm chunks khá chính xác, Retrieval tìm đúng chunk quan trọng (Top-1 thường chứa đáp án).| Test thêm queries, có queries bị lan man không đúng trọng tâm dù tìm đúng đoạn chunk đoạn thông tin cần trả lời, có case bị lost-track information.’Top-K còn nhiều chunk không liên quan → context bị nhiễu |
| Bùi Trần Gia Bảo| DocumentStructureChunker | 6/10| Giữ nguyên cấu trúc tài liệu (heading, section), rất phù hợp với văn bản markdown pháp lý, giúp truy xuất theo ngữ cảnh rõ ràng. | Phụ thuộc vào chất lượng định dạng markdown; nếu cấu trúc không chuẩn hoặc quá dài, chunk có thể mất cân bằng và ảnh hưởng hiệu quả retrieval. |


**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Viết 2-3 câu:*

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> *Viết 2-3 câu: dùng regex gì để detect sentence? Xử lý edge case nào?*

**`RecursiveChunker.chunk` / `_split`** — approach:
> *Viết 2-3 câu: algorithm hoạt động thế nào? Base case là gì?*

### EmbeddingStore

**`add_documents` + `search`** — approach:
> *Viết 2-3 câu: lưu trữ thế nào? Tính similarity ra sao?*

**`search_with_filter` + `delete_document`** — approach:
> *Viết 2-3 câu: filter trước hay sau? Delete bằng cách nào?*

### KnowledgeBaseAgent

**`answer`** — approach:
> *Viết 2-3 câu: prompt structure? Cách inject context?*

### Test Results

```
# Paste output of: pytest tests/ -v
```

**Số tests pass:** __ / __

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | high / low | | |
| 2 | | | high / low | | |
| 3 | | | high / low | | |
| 4 | | | high / low | | |
| 5 | | | high / low | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Viết 2-3 câu:*

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu queries trả về chunk relevant trong top-3?** __ / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
