PIPELINE TONG QUAN

[OFFLINE] Textbooks -> LlamaParse -> Hybrid Indexing (Qdrant + BM25)
                                                     |
[ONLINE]  Question ----------------------------------+--> Step 1: Hybrid RAG -> [Premises]
                                                     |
   +-------------------------------------------------+
   v
Step 2: Reasoner Agent (DeepSeek-R1-7B) -> Sinh suy luan <think> + [FOL] + [Ma Python]
   |
   v
Step 3: Code Sandbox Executor -> Chay ma Python -> Ket qua so hoc & Don vi [Answer]
   |
   v
Step 4: Structuring Agent (Qwen2.5-7B) + Instructor -> Dong goi JSON [CoT], [Explanation]
   |
   v
[API Output Response]


GIAI DOAN 1: CHUAN BI DU LIEU & HUAN LUYEN (OFFLINE)
Do mo hinh kich thuoc nho (<8B) co gioi han ve dung luong tri thuc luu tru trong trong so, can bu dap bang 2 cach: RAG chat luong cao va fine-tuning nhe (LoRA).

1. Xay dung Knowledge Base (ngay khi BTC cong bo tai lieu)
   - Buoc 1.1 (Parsing): Dung LlamaParse hoac Marker de chuyen doi sach giao khoa ly, tai lieu tham khao (PDF) sang Markdown. Dam bao cong thuc toan ly giu nguyen dang LaTeX (vi du: $E = \frac{1}{2}CU^2$).
   - Buoc 1.2 (Chunking): Cat nho tai lieu theo cau truc phan doan (theo tung Dinh luat, Dinh ly, Cong thuc). Moi chunk dai khoang 300-500 tokens.
   - Buoc 1.3 (Indexing): Day du lieu vao DB.
     - Dense embeddings: Dung bge-m3 (chay muot tren local) ma hoa ngu nghia cau hoi.
     - Sparse indexing: Dung RankBM25 luu tu khoa cot loi nhu ky hieu don vi ($\Omega, \mu F, mC$), ten dinh luat (Ohm, Kirchhoff).
     - Vector database: Luu vao Qdrant (open-source, ho tro hybrid search tot).

2. Fine-tuning mo hinh 7B (tuy chon nhung khuyen khich)
   - Tap du lieu cuoc thi cung cap co 5,520 mau co san truong cot, answer, unit.
   - Fine-tune DeepSeek-R1-Distill-Qwen-7B bang Unsloth (toi uu VRAM, co the train tren RTX 3090/4090).
   - Muc tieu: Day mo hinh 7B format dau ra chuan hoa (luon sinh FOL, luon sinh code Python theo dinh dang dinh san, khop phong cach giai ly cua tap du lieu goc).


GIAI DOAN 2: LUONG THUC THI ONLINE TREN ENDPOINT API (ONLINE INFERENCE)
Khi endpoint API nhan duoc cau hoi (question), he thong kich hoat workflow gom 4 buoc (qua LangGraph hoac vong lap code tuan tu):

Buoc 1: Trich xuat tien de (Premise Identification via Hybrid RAG)
   - Thuc hien hybrid search vao Qdrant de tim 2-3 cong thuc/dinh luat lien quan nhat.
   - Dau ra: mang chuoi tien de. Vi du: ["Ohm's law: V = I * R", "Capacitor Energy: E = 0.5 * C * U^2"].
   - Cac chuoi nay duoc dien thang vao truong "premises".

Buoc 2: Suy luan & sinh ma giai (Reasoning & Code Generation)
   - Nap cau hoi va premises vao DeepSeek-R1-Distill-Qwen-7B.
   - Mo hinh kich hoat suy luan tung buoc qua the an <think>.
   - Prompt yeu cau 2 thanh phan:
     - FOL (First-Order Logic): Mo ta bai toan duoi dang logic vi tu.
     - Ma nguon Python: Chuyen bai toan thanh kich ban tinh toan (bao gom doi don vi, vi du $\mu F -> F$).

Buoc 3: Dam bao tinh chinh xac 100% (Sandbox Execution)
   - Boc tach doan ma Python tu Buoc 2.
   - Chay trong moi truong co lap (RestrictedPython hoac exec() co kiem soat I/O).
   - Ly do: Mo hinh 7B tinh toan so thap phan kem (vi du nhan so mu am $10^{-6}$ de lech dau phay).
   - Dau ra: gia tri so hoc chinh xac (vi du 0.045) va don vi (J), gop lai thanh truong "answer".

Buoc 4: Dong goi va dinh dang JSON (Structured Generation)
   - Dung Qwen2.5-7B-Instruct + Instructor (Pydantic) de cau truc hoa JSON.
   - Mo hinh doc: <think> tu Buoc 2 va ket qua chay code tu Buoc 3.
   - Tao mang "cot" (cac buoc tuong minh de doc) va viet "explanation" (giai thich tu nhien, toi uu diem P2).
   - Cham diem "confidence" dua tren viec code Python chay thanh cong, khong loi cu phap hoac toan hoc.