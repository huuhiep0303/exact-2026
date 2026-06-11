# EXACT 2026 - Submission Guide

**The 2nd International XAI Challenge for Transparent Educational Question-Answering**
**IEEE IJCNN 2026 Competition**

> Tài liệu này giải thích cách đóng gói và nộp hệ thống để đánh giá. Vui lòng đọc kỹ, vì các bài nộp không đúng định dạng có thể bị lỗi khi đánh giá tự động.

---

## 1. Tổng quan

Hệ thống của bạn được đánh giá dưới dạng một **HTTP API endpoint trực tiếp**. Trong suốt khung giờ chấm điểm, server đánh giá sẽ gửi truy vấn đến endpoint và thu thập phản hồi.

### Yêu cầu endpoint

Endpoint của bạn phải:

1. Có thể truy cập công khai qua internet
2. Nhận truy vấn đúng định dạng mô tả bên dưới
3. Trả về phản hồi theo JSON schema yêu cầu
4. Phản hồi trong vòng **60 giây** mỗi request
5. Hoạt động liên tục trong toàn bộ khung giờ chấm điểm đã đăng ký

### Quy tắc đánh giá

- **Mỗi truy vấn gọi một lần:** Mỗi truy vấn chỉ được gửi đúng một lần, không có retry. Nếu một lần gọi thất bại hoặc timeout, truy vấn đó bị tính là trả lời sai.
- **Timeout 60 giây:** Bất kỳ phản hồi nào mất hơn 60 giây đều bị tính là thất bại.
- **Tuần tự, từng đội một:** Truy vấn được gửi tuần tự (lần lượt, không song song), và mỗi đội được đánh giá trong khung giờ riêng. Điều này giúp tải hệ thống ổn định và đảm bảo công bằng vì bonus tốc độ được đo trong cùng điều kiện.

### Cấu trúc bộ test

Bộ test gồm **50 câu hỏi**: 25 câu Type 1 (Logic-Based Educational Queries) và 25 câu Type 2 (Physics Problems). Tất cả 50 câu được gửi đến endpoint `/predict` duy nhất của bạn trong khung giờ chấm điểm. Sau khi chấm, ban tổ chức sẽ trả lại cho bạn các câu trả lời mà mô hình đã tạo ra.

---

## 2. Các Endpoint Yêu Cầu

Hệ thống của bạn cần expose một endpoint dự đoán (do bạn xây dựng) và một endpoint thông tin mô hình (do vLLM cung cấp tự động).

### 2.1 Prediction Endpoint (do bạn xây dựng)

Đây là endpoint giải pháp duy nhất. Nó nhận mọi truy vấn thi đấu và trả về câu trả lời kèm giải thích.

```
POST https://<your-host>/predict
Content-Type: application/json
```

Đây là một endpoint duy nhất xử lý cả Type 1 và Type 2. Bạn **không** tạo endpoint riêng cho từng loại. Khi request đến, bạn đọc trường `type` và route nội bộ đến pipeline phù hợp:

```
POST /predict
 |
 +-- if type == "type1" -> logic pipeline (FOL + solver)
 +-- if type == "type2" -> physics pipeline (compute + CoT)
```

Đường dẫn endpoint có thể tùy chỉnh (`/predict`, `/`, `/api/solve`, v.v.); chỉ cần cung cấp URL chính xác. Bên trong có thể gọi vLLM server, symbolic solvers, retrieval modules, code execution, v.v. Điều quan trọng là URL này nhận đúng định dạng input và trả về đúng định dạng output của cuộc thi.

### 2.2 Model Info Endpoint (do vLLM cung cấp, không phải do bạn xây dựng)

Bạn **không** cần code endpoint này. Khi bạn khởi động mô hình với `vllm serve`, vLLM tự động expose một endpoint chuẩn liệt kê mô hình đang chạy:

```
GET https://<your-vllm-host>/v1/models
```

Bạn chỉ cần đảm bảo endpoint này có thể truy cập bởi ban tổ chức để xác minh mô hình đang chạy. Nếu bạn dùng nhiều hơn một mô hình (được phép, miễn là tổng kích thước đang chạy tại bất kỳ thời điểm nào không vượt quá 8B), mỗi vLLM server có URL `/v1/models` riêng.

Bạn liệt kê tất cả các URL (URL dự đoán và mọi URL `/v1/models`) trong một file text duy nhất bên trong gói nộp bài (xem Mục 8).

---

## 3. Định dạng Input

Server đánh giá gửi POST request đến endpoint `/predict` của bạn. Request body là một JSON object duy nhất. Chúng tôi dùng một schema thống nhất cho cả hai loại truy vấn: mọi trường đều luôn có mặt, và các trường không áp dụng được để trống (`""` hoặc `[]`).

### 3.1 Unified Input Schema

```json
{
  "query_id": "T1_0001",
  "type": "type1",
  "query": "Is Student A eligible for graduation?",
  "premises": [
    "A student who has completed at least 120 credits is eligible for graduation.",
    "Student A has completed 118 credits."
  ],
  "options": ["Yes", "No", "Uncertain"]
}
```

### 3.2 Định nghĩa các trường

| Trường | Kiểu | Mô tả | Khi nào rỗng |
|--------|------|-------|--------------|
| `query_id` | string | Định danh truy vấn duy nhất | Không bao giờ |
| `type` | string | `"type1"` hoặc `"type2"` | Không bao giờ |
| `query` | string | Câu hỏi (Type 1) hoặc đề bài đầy đủ (Type 2) | Không bao giờ |
| `premises` | list | Các tiền đề ngôn ngữ tự nhiên, đánh số từ 0. Tham chiếu các chỉ số này trong `premises_used` | `[]` với Type 2 |
| `options` | list | Tập hợp lựa chọn cho câu hỏi trắc nghiệm | `[]` với câu hỏi số/văn bản và Type 2 |

**Cách đọc `options`:**
- Nếu `options` không rỗng → câu hỏi lựa chọn. Câu trả lời phải **chính xác là một** trong các lựa chọn liệt kê.
- Nếu `options` rỗng (`[]`) → câu trả lời tự do (số hoặc văn bản ngắn). Trả giá trị trực tiếp trong `answer`.

### 3.3 Ví dụ

**Type 1 — câu hỏi lựa chọn (`options` không rỗng):**

```json
{
  "query_id": "T1_0001",
  "type": "type1",
  "query": "Is Student A eligible for graduation?",
  "premises": ["A student with >= 120 credits is eligible.", "Student A has 118 credits."],
  "options": ["Yes", "No", "Uncertain"]
}
```

**Type 1 — câu hỏi số/văn bản (`options` rỗng):**

```json
{
  "query_id": "T1_0002",
  "type": "type1",
  "query": "How many more credits does Student A need to graduate?",
  "premises": ["A student with >= 120 credits is eligible.", "Student A has 118 credits."],
  "options": []
}
```

**Type 2 — bài toán vật lý (`premises` và `options` đều rỗng):**

```json
{
  "query_id": "T2_0001",
  "type": "type2",
  "query": "Two resistors R1 = 4 ohm and R2 = 6 ohm are in parallel across a 12V battery. Find the total current.",
  "premises": [],
  "options": []
}
```

> **Lưu ý quan trọng:** Endpoint `/predict` duy nhất của bạn phải xử lý cả hai loại truy vấn. Dùng trường `type` để route request đến pipeline nội bộ phù hợp.

---

## 4. Định dạng Output

Endpoint của bạn phải trả về một **JSON list** chứa một object kết quả cho mỗi truy vấn. Ngay cả với một truy vấn duy nhất, vẫn trả về list với một phần tử. Tương tự input, chúng tôi dùng một schema thống nhất: mọi trường đều luôn có mặt, và các trường không áp dụng được để trống.

### 4.1 Unified Output Schema

```json
[
  {
    "query_id": "T1_0001",
    "answer": "No",
    "unit": "",
    "explanation": "The eligibility rule requires at least 120 credits, but Student A has only 118, which is below the threshold. Therefore Student A is not eligible.",
    "premises_used": [0, 1],
    "reasoning": {
      "type": "fol",
      "steps": [
        "Rule: Credits(x) >= 120 => Eligible(x)",
        "Fact: Credits(StudentA) = 118",
        "118 < 120, premise not satisfied",
        "Conclusion: not Eligible(StudentA)"
      ]
    }
  }
]
```

Trong input ở trên, `premises[0]` là quy tắc đủ điều kiện và `premises[1]` là sự kiện về tín chỉ của Student A. Vì cả hai đều được dùng để suy ra câu trả lời, `premises_used` là `[0, 1]`.

### 4.2 Định nghĩa các trường

| Trường | Kiểu | Mô tả | Khi nào rỗng |
|--------|------|-------|--------------|
| `query_id` | string | Phải khớp với `query_id` từ input | Không bao giờ |
| `answer` | string | Câu trả lời cuối cùng. Type 1: lựa chọn, số, hoặc văn bản. Type 2: chỉ giá trị số (đơn vị đặt trong `unit`) | Không bao giờ |
| `unit` | string | Đơn vị câu trả lời, dùng ASCII (ví dụ: `A`, `V`, `ohm`, `V/m`, `J`, `W`, `uF`, `nC`) | `""` với Type 1 |
| `explanation` | string | Giải thích ngôn ngữ tự nhiên. Không được để trống hoặc null, dù không được chấm điểm trong vòng này | Không bao giờ |
| `premises_used` | list of int | Chỉ số 0-based của các premises (từ mảng `premises` input) thực sự được dùng để suy ra câu trả lời | `[]` với Type 2 |
| `reasoning` | object | Bằng chứng lý luận có cấu trúc (tùy chọn). Dùng `null` nếu không cung cấp | `null` nếu không dùng |

### 4.3 Ví dụ

**Phản hồi Type 1** (`unit` rỗng, `premises_used` là chỉ số 0-based):

```json
[
  {
    "query_id": "T1_0001",
    "answer": "No",
    "unit": "",
    "explanation": "Student A has 118 credits, below the 120 required, so not eligible.",
    "premises_used": [0, 1],
    "reasoning": { "type": "fol", "steps": ["118 < 120", "not Eligible(StudentA)"] }
  }
]
```

**Phản hồi Type 2** (`unit` được điền, `premises_used` rỗng):

```json
[
  {
    "query_id": "T2_0001",
    "answer": "5",
    "unit": "A",
    "explanation": "Two resistors in parallel give 2.4 ohm; 12V / 2.4 ohm = 5 A.",
    "premises_used": [],
    "reasoning": {
      "type": "cot",
      "steps": [
        "1/Req = 1/4 + 1/6 = 5/12",
        "Req = 2.4 ohm",
        "I = 12 / 2.4 = 5 A"
      ]
    }
  }
]
```

### 4.4 Object `reasoning` (Tùy chọn)

```json
"reasoning": {
  "type": "fol",
  "steps": ["...", "..."]
}
```

- **`type`**: loại phù hợp với hệ thống của bạn, ví dụ: `"fol"` (First-Order Logic), `"cot"` (Chain-of-Thought), hoặc `"proof"` (structured proof)
- **`steps`**: danh sách các bước lý luận

Trường này là tùy chọn trong vòng này (dùng `null` nếu không cung cấp) nhưng được khuyến nghị, vì nó sẽ quan trọng cho đánh giá độ sâu lý luận (P3) trong các giai đoạn sau.

### 4.5 Cách tính điểm trong vòng này

**Điểm cơ bản:**

| Loại | Tiêu chí | Trọng số |
|------|----------|----------|
| Type 1 | P1: độ chính xác của `answer` | 50% |
| Type 1 | P2: độ chính xác của `premises_used` | 50% |
| Type 2 | P1: cả `answer` và `unit` đều đúng | 100% |

Với Type 2, cả giá trị số và đơn vị đều phải đúng để được điểm. Dùng đơn vị ASCII chuẩn để đảm bảo matching chính xác.

Trường `explanation` bắt buộc phải có nhưng không được chấm điểm trong vòng này. Vẫn phải có mặt và không được để trống.

**Điểm thưởng** (cộng thêm vào điểm cơ bản):

| Bonus | Tối đa | Điều kiện |
|-------|--------|-----------|
| Sửa dataset | +10% | Báo cáo vấn đề dataset được xác minh (xem Q22 trong Official Q&A) |
| Tốc độ inference | +10% | Dựa trên thời gian inference trung bình, chỉ tính trên các truy vấn trả lời đúng |

> **Lưu ý về bonus tốc độ:** Tốc độ chỉ được đo trên các truy vấn trả lời đúng. Trả lời nhanh nhưng sai (hoặc rỗng) không được tính bonus tốc độ. Điều này ngăn việc hy sinh độ chính xác để lấy tốc độ.

---

## 5. Notation Mapping (Công bằng về Ký hiệu & Đơn vị)

Để đảm bảo công bằng trong cách khớp ký hiệu toán học và đơn vị, ban tổ chức sẽ cung cấp một **Notation Mapping CSV** trước giai đoạn đánh giá.

### 5.1 Cách hoạt động

Ban tổ chức cung cấp một file CSV riêng với ba cột:

| Cột | Mô tả |
|-----|-------|
| `canonical_latex` | Dạng LaTeX chuẩn như trong dataset |
| `meaning` | Mô tả thuần túy của ký hiệu |
| `your_notation` | Bạn điền ký hiệu chính xác mà mô hình của bạn mong đợi (để trống để dùng dạng chuẩn) |

Trước khi gửi truy vấn đến endpoint của bạn, ban tổ chức sẽ regex-replace ký hiệu trong đề bài của chúng tôi bằng ký hiệu bạn khai báo. Bạn chỉ cần điền các hàng nơi quy ước của bạn khác với dạng chuẩn; các hàng trống được giữ nguyên.

### 5.2 Các ký hiệu có thể xuất hiện trong đề bài

**Toán tử số học và đại số:**
`+`, `-`, `\times` (nhân), `\cdot` (nhân chấm), `\div` (chia), `/` (phân số), `\pm`, `\mp`, `=`, `\approx`, `\neq`, `<`, `>`, `\leq`, `\geq`, `\propto` (tỷ lệ thuận), `\infty`

**Lũy thừa, căn, phân số, ký hiệu khoa học:**
`a^b` (lũy thừa/superscript), `a_b` (subscript), `\sqrt{}` (căn bậc hai), `\sqrt[n]{}` (căn bậc n), `\frac{a}{b}` (phân số), `\times 10^{n}` (ký hiệu khoa học, ví dụ: `3 \times 10^{-6}`)

**Chữ Hy Lạp** (phổ biến trong mạch điện và tĩnh điện):
`\alpha`, `\beta`, `\gamma`, `\delta`, `\Delta` (độ biến thiên), `\epsilon`/`\varepsilon` (permittivity), `\theta`, `\lambda` (mật độ điện tích tuyến tính), `\mu` (tiền tố micro/permeability), `\pi`, `\rho` (điện trở suất/mật độ điện tích khối), `\sigma` (độ dẫn điện/mật độ điện tích mặt), `\tau` (hằng số thời gian), `\phi`/`\varphi` (điện thế/thông lượng), `\Phi` (thông lượng), `\omega` (tần số góc), `\Omega` (ohm)

**Ký hiệu giải tích và vector:**
`\int` (tích phân), `\sum` (tổng), `\partial` (đạo hàm riêng), `\nabla` (nabla/del), `\vec{}` (vector), `\hat{}` (vector đơn vị)

**Đơn vị** (mạch điện và tĩnh điện):
`V` (volt), `A` (ampere), `\Omega`/`ohm` (ohm), `W` (watt), `J` (joule), `C` (coulomb), `F` (farad), `H` (henry), `T` (tesla), `Wb` (weber), `N` (newton), `V/m`, `N/C`, `Hz`, `s`, `m`, `eV`

**Tiền tố hệ mét:**
`p` (pico), `n` (nano), `\mu`/`u` (micro), `m` (milli), `k` (kilo), `M` (mega), `G` (giga)

**Ký hiệu khác:**
`\degree`/`°` (độ), `\%` (phần trăm), `\angle` (góc)

> **Về đơn vị trong câu trả lời:** Trường `unit` trong phản hồi Type 2 phải dùng ASCII chuẩn (ví dụ: `V/m`, `ohm`, `uF`, `nC`).

---

## 6. Model Serving & Xác minh (vLLM)

Để đảm bảo công bằng, tất cả các thành phần LLM phải được serve qua **vLLM** hoặc một framework tương thích kiểu OpenAI.

### 6.1 Tại sao dùng vLLM

Vì một API endpoint là hộp đen, chúng tôi cần một cách chuẩn để xác nhận mô hình nào thực sự đang chạy. vLLM expose endpoint `/v1/models` chuẩn báo cáo mô hình đã tải. Điều này ngăn các đội bí mật route đến mô hình lớn hơn.

### 6.2 Những gì bạn cần làm

Khởi động mô hình của bạn với vLLM, ví dụ:

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000
```

Đảm bảo endpoint `/v1/models` có thể truy cập bởi ban tổ chức:

```bash
curl https://<your-vllm-host>/v1/models
```

Kết quả trả về sẽ như sau:

```json
{
  "object": "list",
  "data": [
    {
      "id": "meta-llama/Llama-3.1-8B-Instruct",
      "object": "model",
      "owned_by": "vllm"
    }
  ]
}
```

`id` phải khớp với mô hình bạn khai báo trong mô tả giải pháp. **Các API inference của bên thứ ba** (Together AI, Fireworks, Groq, Replicate, v.v.) **không được phép** vì không thể xác minh danh tính mô hình.

### 6.3 Sử dụng nhiều hơn một mô hình

Ràng buộc là về tổng dung lượng: tại bất kỳ thời điểm nào trong quá trình inference, **tổng tham số của tất cả LLM đang tải và chạy cùng lúc phải ≤ 8B**.

| Trường hợp | Phép/Không phép |
|------------|-----------------|
| Mô hình 8B cho Type 1 và mô hình 8B riêng cho Type 2 dùng lần lượt (tuần tự) | ✅ Được phép |
| Hai mô hình 4B chạy song song (tổng 8B, trong giới hạn) | ✅ Được phép |
| Hai mô hình 8B chạy song song (tổng 16B, vượt giới hạn) | ❌ Không được phép |
| Bất kỳ cấu hình nào có tổng active size vượt 8B | ❌ Không được phép |

Nếu dùng nhiều hơn một mô hình:
- Khai báo **mọi mô hình** trong mô tả giải pháp kèm số tham số
- Cung cấp URL `/v1/models` cho mỗi vLLM server
- Với mô hình MoE, đếm **tổng tham số** (không phải tham số active, xem Q2)
- Các công cụ không phải LLM (solvers, retrieval, code execution) **không tính** vào giới hạn

---

## 7. Đăng ký Khung giờ Chấm điểm & Cửa sổ Hosting

> **Deadline nộp bài đã được gia hạn đến ngày 12 tháng 6 năm 2026.**

Để tổ chức đánh giá có trật tự, ban tổ chức sẽ mở form đăng ký khung giờ. Mỗi đội đăng ký một khung giờ, và mỗi khung giờ kéo dài **một tiếng**.

**Điều này có nghĩa gì với bạn:**
- Bạn chỉ cần giữ API endpoint(s) online trong khung giờ một tiếng đó, không phải toàn bộ giai đoạn.
- Trong khung giờ của bạn, server đánh giá sẽ gửi tất cả 50 truy vấn test đến endpoint `/predict` và có thể kiểm tra endpoint(s) `/v1/models` của bạn.
- Đảm bảo endpoint ổn định và có thể truy cập trong suốt một tiếng đã chọn.
- Sau khi chấm điểm, ban tổ chức sẽ trả lại các câu trả lời mà mô hình của bạn đã tạo ra.
- Nếu bạn bỏ lỡ khung giờ, hãy liên hệ ban tổ chức trên Discord (`#technical-support`) càng sớm càng tốt; việc đổi lịch tùy thuộc vào sự sẵn có.

Form đăng ký khung giờ và các cửa sổ thời gian available sẽ được thông báo trên Discord và website chính thức.

---

## 8. Gói Nộp Bài

Đóng gói mọi thứ vào một file ZIP duy nhất đặt tên theo tên đội: `<team_name>.zip`.

**Deadline nộp bài: 12 tháng 6 năm 2026.**
**Email backup:** ura.hcmut@gmail.com

### Cấu trúc file ZIP

`<team_name>.zip` phải chứa:

1. **`solution.pdf`** — Mô tả giải pháp (một trang, PDF) phải bao gồm:
   - **Datasets đã dùng:** với mỗi dataset, ghi rõ tên, nguồn/xuất xứ, số lượng mẫu đã dùng, và vài mục mẫu. Bao gồm cả dataset EXACT chính thức lẫn dữ liệu ngoài, crawled, hoặc synthetic.
   - **Approach và phương pháp:** tổng quan rõ ràng về pipeline (hiểu đề, lý luận, tạo giải thích).
   - **Tính toán kích thước mô hình:** liệt kê mọi LLM trong pipeline kèm số tham số, và chứng minh tổng đang tải và chạy tại bất kỳ thời điểm nào ≤ 8B.

2. **`source_code.zip`** — Mã nguồn (nén thành .zip)

3. **`urls.txt`** — File text chứa URL dự đoán và mọi URL `/v1/models`

4. **`notation_mapping.csv`** — CSV Notation Mapping điền với quy ước ký hiệu của bạn (xem Mục 5)

### Cấu trúc ví dụ

```
<team_name>.zip
├── solution.pdf
├── source_code.zip
├── urls.txt
└── notation_mapping.csv
```

---

## 9. Checklist Trước Khi Nộp

Trước khi nộp, xác nhận các mục sau:

**Về endpoint:**
- [ ] `/predict` chấp nhận cả truy vấn Type 1 và Type 2 (route bằng `type`)
- [ ] `/predict` trả về JSON list các result objects
- [ ] Mỗi result bao gồm `query_id`, `answer`, `explanation`, và `premises_used`
- [ ] Câu hỏi lựa chọn (`options` không rỗng): `answer` là chính xác một trong các lựa chọn
- [ ] Type 1: `premises_used` chứa chỉ số 0-based của các premises thực sự dùng
- [ ] Type 2: có trường `unit` dùng ASCII, và `premises_used` là `[]`
- [ ] `explanation` có mặt và không rỗng (không null)
- [ ] `query_id` trong phản hồi khớp với input
- [ ] Phản hồi đến trong vòng 60 giây (mỗi truy vấn chỉ gọi một lần, không retry)
- [ ] Endpoint ổn định với các request tuần tự, từng cái một

**Về mô hình:**
- [ ] Mọi vLLM server expose `/v1/models` có thể truy cập báo cáo mô hình đã khai báo
- [ ] Tất cả mô hình đang serve là open-source
- [ ] Tổng tham số của tất cả LLM đang tải và chạy tại bất kỳ thời điểm nào ≤ 8B

**Về đăng ký và nộp bài:**
- [ ] Đã đăng ký một khung giờ chấm điểm một tiếng qua form
- [ ] Endpoint(s) sẽ online trong toàn bộ khung giờ
- [ ] File ZIP nộp bài đặt tên `<team_name>.zip` chứa: `solution.pdf`, source code zip, `urls.txt`, `notation_mapping.csv`
- [ ] Solution PDF liệt kê mỗi dataset với nguồn và số mẫu đã dùng
- [ ] Solution PDF bao gồm tính toán tổng tham số chứng minh giải pháp trong giới hạn 8B
- [ ] Notation Mapping CSV đã điền với quy ước ký hiệu của bạn
- [ ] Nộp bài trước deadline 12 tháng 6 năm 2026

---

## 10. Luồng Tham chiếu Đơn giản

```
Evaluation Server
 |
 | POST /predict { query_id, type, query, premises, options }
 v
Your /predict endpoint
 |
 |-- route by type
 |   |
 |   +-- type1: NL + premises -> FOL -> solver -> answer + premises_used (indices)
 |   |         (if options non-empty, answer must be one of them)
 |   +-- type2: parse -> compute (code/CoT) -> answer + unit
 |
 | (internally calls your vLLM server(s) as needed)
 v
Return [ { query_id, answer, unit, explanation, premises_used, reasoning } ]
```
