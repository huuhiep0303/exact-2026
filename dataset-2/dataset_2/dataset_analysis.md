# 📊 Phân Tích Tổng Quan Dataset: `Physics_Problems_Text_Only.csv`

> **Ngày phân tích:** 2026-05-18  
> **File nguồn:** `dataset_2/Physics_Problems_Text_Only.csv`  
> **Kích thước file:** ~1.07 MB  
> **Tổng số dòng (rows):** 7,353 dòng (bao gồm header + các dòng CoT nội tuyến)  
> **Tổng số câu hỏi:** **1,352 câu hỏi**

## 0. Lỗi Sai Đang Gặp Phải

---

### 🔴 Vấn đề 1: 14 Câu Thiếu Đơn Vị (`unit` rỗng)

| ID | Answer | Đơn vị đúng cần điền | Nội dung câu hỏi |
|----|--------|----------------------|-----------------|
| TD013 | 5.28 | *(dimensionless)* | Tìm hằng số điện môi κ từ C, A, d |
| DT047 | `1/2.(1/√E_A + 1/√E_B)` | m | Tìm điểm M trên đường sức có E = 0 |
| TD369 | Do not change | *(mô tả)* | Tụ ngắt nguồn, thay bản tụ – điện trường thay đổi thế nào? |
| TD373 | 50% | % | Tụ được thay thế – năng lượng thay đổi bao nhiêu %? |
| TD377 | the voltage is halfed | *(mô tả)* | Tụ Q không đổi, C tăng gấp đôi – U thay đổi thế nào? |
| TD380 | decreases by 4 times | *(mô tả)* | Tụ Q giảm một nửa – năng lượng thay đổi thế nào? |
| TD386 | decreases by half | *(mô tả)* | Tụ nằm trong điện môi ε=4, tăng d – E thay đổi thế nào? |
| DDT327 | 0.60 | *(dimensionless)* | Tính hệ số công suất cosφ (R=12Ω, Z=20Ω) |
| DDT337 | 0.60 | *(dimensionless)* | Tính cosφ (R=18Ω, Z=30Ω) |
| DDT343 | 0.40 | *(dimensionless)* | Tính cosφ (R=16Ω, Z=40Ω) |
| CH371 | 1.12 | *(dimensionless)* | Tính hệ số phẩm chất Q (L=0.1H, C=50µF, R=40Ω) |
| CH372 | 1.00 | *(dimensionless)* | Tính Q (L=0.2H, C=80µF, R=50Ω) |
| CH373 | 1.77 | *(dimensionless)* | Tính Q (L=0.05H, C=40µF, R=20Ω) |
| CH374 | 2.11 | *(dimensionless)* | Tính Q (L=0.12H, C=30µF, R=30Ω) |

> **Nhận xét:** Phần lớn là các đại lượng **không có đơn vị** (hằng số điện môi, hệ số công suất cosφ, hệ số phẩm chất Q) hoặc **đáp án mô tả** (descriptive). Nên thêm `—` hoặc `dimensionless` cho các trường hợp này.

---

### 🟡 Vấn đề 3: Đơn Vị Không Đồng Nhất

#### 3a. `μF` (U+03BC·F) vs `µF` (U+00B5·F) — 2 ký tự Greek khác nhau

Cả hai đều là microFarad nhưng dùng ký tự Unicode khác nhau:
- `μF` = **U+03BC** (Greek Small Letter Mu) — **41 câu** *(chuẩn)*  
- `µF` = **U+00B5** (Micro Sign) — **14 câu** *(cần chuẩn hóa)*

| ID dùng `µF` (cần sửa) |
|------------------------|
| NL319, NL333, NL344, NL353, NL370, NL395 |
| CH349, CH350, CH351, CH352, CH353, CH354, CH355, CH356 |

#### 3b. `-` (hyphen) vs `—` (em-dash) — cùng nghĩa "không đơn vị"

| Ký tự | Unicode | Số câu | Ý nghĩa |
|-------|---------|:------:|---------|
| `-` | U+002D (Hyphen-Minus) | **84 câu** | Đáp án không có đơn vị *(chuẩn dùng)* |
| `—` | U+2014 (Em Dash) | **42 câu** | Đáp án không có đơn vị *(cần chuẩn hóa về `-`)* |

Một số ID dùng `—` (em-dash): `TD093, TD094, TD098, TD100, THCB071, THCB073, THCB081, THCB083, NL025, NL026, NL095, NL100, NL105, NL119, NL120, ...`

---

### 🟠 Vấn đề 5: 182 Đáp Án Dạng Biểu Thức (Không Thuần Số)

Tổng cộng **182 câu** có đáp án không phải số thuần túy. Chia thành 3 nhóm:

#### Nhóm A – LaTeX / Ký hiệu Toán học (9 câu)
Đáp án chứa `\sqrt`, `\frac`, ký hiệu vật lý → cần parser LaTeX khi đánh giá model.

| ID | Đáp án | Đơn vị |
|----|--------|--------|
| LD005 | `9\sqrt{3} × 10^-27` | N |
| LD041 | `\sqrt{2} × F₀` | N |
| LD085 | `2 × sqrt(2) × k × q / a^2` | — |
| LD087 | `-2\sqrt{2} x q` | — |
| DT007 | `a/ \sqrt{2}` | m |
| DT008 | `/frac{2k \abs{q} h}{(a^2 + h^2)^1.5}` | V/m |
| DT020 | `\frac{4 \sqrt{2} k q}{\epsilon a^2}` | V/m |
| DT047 | `1/2 . (1/ \sqrt{E_A} + 1/ \sqrt{E_B})` | *(trống)* |
| DT060 | `1/4 \pi` | rad |

#### Nhóm B – Đáp án mô tả bằng văn bản (≈88 câu)
Đáp án là câu giải thích định tính → không thể so khớp số, cần đánh giá bằng NLP/LLM.

*Ví dụ:*
| ID | Đáp án |
|----|--------|
| LD047 | `Hướng về phía q₂` |
| TD369 | `Do not change` |
| TD377 | `the voltage is halfed` |
| TD380 | `decreases by 4 times` |
| TD386 | `decreases by half` |
| THCB071 | `Resistance decreases → current increases.` |
| THCB073 | `The lamp shines brighter because the current through it increases.` |
| NL025 | `all energy is entirely stored in the magnetic field` |
| NL026 | `all energy is entirely stored in the electric field` |

#### Nhóm C – Số có ký tự `×`, `⁰`, `⁻`, superscript (≈85 câu)
Đáp án dạng `4.0 × 10⁴`, `1.00 × 10⁷` — về bản chất là số nhưng dùng ký tự Unicode đặc biệt thay cho `e` notation.

*Ví dụ:* `LD294→ 0.230 × 10⁻³`, `LD338→ 1.00 × 10⁷`, `TD390→ 1.2×10⁵`

> **Khuyến nghị:** Chuẩn hóa nhóm C về dạng `float` hoặc `scientific notation` (e.g., `2.3e-4`). Nhóm A cần render LaTeX. Nhóm B cần xử lý riêng như bài toán classification/generation.

---



## 1. Cấu Trúc Dataset

Dataset có **5 cột** chính:

| Cột | Ý nghĩa | Kiểu dữ liệu |
|-----|---------|--------------|
| `id` | Mã định danh câu hỏi (Prefix + Số) | String |
| `question` | Nội dung câu hỏi vật lý | String |
| `cot` | Chuỗi suy luận từng bước (Chain-of-Thought) | String (multi-step) |
| `answer` | Đáp án số hoặc ký hiệu | String/Numeric |
| `unit` | Đơn vị của đáp án | String |

---

## 2. Phân Loại Mã (Prefix) và Chủ Đề

Dataset có **8 mã prefix** tương ứng với 8 chủ đề/lĩnh vực vật lý:

| Mã | Chủ đề / Lĩnh vực | Số câu hỏi | Phạm vi ID |
|----|-------------------|:-----------:|------------|
| **LD** | Tĩnh điện học – Lực Coulomb & Điện trường | 397 | LD001 – LD400 |
| **CH** | Mạch điện xoay chiều (AC) – RLC, công suất, tổng trở | 290 | CH001 – CH380 |
| **NL** | Dao động điện từ – Năng lượng tụ/cuộn cảm, mạch LC | 190 | NL001 – NL400 |
| **TD** | Tụ điện phẳng – Điện dung, điện tích, điện trường | 177 | TD001 – TD402 |
| **DDT** | Từ trường & Cảm ứng điện từ – Solenoid, từ thông, cảm kháng | 130 | DDT131 – DDT400 |
| **THCB** | Thực hành & Sai số đo lường | 80 | THCB001 – THCB135 |
| **DT** | Điện thế & Hiệu điện thế (điểm trên đường sức) | 68 | DT001 – DT100 |
| **CHLT** | Mạch AC – Bài toán cộng hưởng nâng cao | 20 | CHLT001 – CHLT020 |

**Tổng cộng:** **1,352 câu hỏi**

### 🔢 Biểu đồ phân bố (ASCII)
```
LD    ████████████████████████████████████████ 397
CH    █████████████████████████████ 290
NL    ███████████████████ 190
TD    █████████████████ 177
DDT   █████████████ 130
THCB  ████████ 80
DT    ██████ 68
CHLT  ██ 20
      0   50  100 150 200 250 300 350 400
```

---

## 3. Số Câu Hỏi Theo Từng Mã

| Mã | Số câu hỏi | % tổng dataset |
|----|:-----------:|:--------------:|
| LD | 397 | 29.4% |
| CH | 290 | 21.4% |
| NL | 190 | 14.1% |
| TD | 177 | 13.1% |
| DDT | 130 | 9.6% |
| THCB | 80 | 5.9% |
| DT | 68 | 5.0% |
| CHLT | 20 | 1.5% |
| **Tổng** | **1,352** | **100%** |

---

## 4. Phân Phối Đơn Vị Đáp Án

| Đơn vị | Số lượng | Mã chủ yếu |
|--------|:--------:|-----------|
| N (Newton) | 248 | LD |
| V/m (Volt/mét) | 171 | LD, DT |
| - (không đơn vị / tỉ lệ) | 84 | CH, CHLT |
| V (Volt) | 76 | CH, NL, TD, DDT |
| J (Joule) | 70 | NL |
| Ω (Ohm) | 68 | CH, DDT |
| A (Ampere) | 63 | CH, THCB |
| W (Watt) | 61 | CH, DDT |
| — (dạng biểu thức) | 42 | DDT |
| μF (microFarad) | 41 | TD, NL, CH |
| nC (nanoCoulomb) | 40 | TD |
| pF (picoFarad) | 40 | TD |
| % (phần trăm) | 39 | THCB |
| mJ (milliJoule) | 37 | NL |
| nJ (nanoJoule) | 35 | TD |
| Hz (Hertz) | 30 | CH |
| H (Henry) | 29 | NL, DDT |
| N/C | 15 | LD, DT |
| T (Tesla) | 10 | DDT |
| Wb (Weber) | 10 | DDT |

---

## 5. Công Thức Cốt Lõi Theo Từng Mã

### 5.1 LD – Tĩnh Điện Học (Lực & Điện Trường)

| Đại lượng | Công thức | Ghi chú |
|-----------|-----------|---------|
| Lực Coulomb | `F = k × |q₁ × q₂| / r²` | k = 9×10⁹ N·m²/C² |
| Cường độ điện trường | `E = k × |q| / r²` | Đơn vị V/m |
| Nguyên lý chồng chất | `E⃗ = E⃗₁ + E⃗₂ + ... + E⃗ₙ` | Cộng vector |
| Hợp lực 2 lực cùng phương | `F = F₁ + F₂` | Cùng chiều |
| Hợp lực 2 lực vuông góc | `F = √(F₁² + F₂²)` | Pythagoras |
| Hợp lực 2 lực bất kỳ | `F = √(F₁² + F₂² + 2F₁F₂cosθ)` | Định lý Cosine |
| Lực tại điểm bất kỳ | `F = q₀ × E` | q₀ là điện tích thử |
| Điện trường = 0 | Giải hệ phương trình `E₁ = E₂` (hướng ngược nhau) | |

> **Đặc điểm LD:** Chiếm ~30% dataset. Tập trung vào bài toán hình học (tam giác vuông, đều, vuông cân) và tìm vector hợp lực/điện trường.

---

### 5.2 CH – Mạch Điện Xoay Chiều

| Đại lượng | Công thức | Ghi chú |
|-----------|-----------|---------|
| Tổng trở | `Z = √(R² + (X_L - X_C)²)` | |
| Cảm kháng | `X_L = ω·L = 2πf·L` | |
| Dung kháng | `X_C = 1/(ω·C) = 1/(2πf·C)` | |
| Cường độ hiệu dụng | `I = U / Z` | |
| Điện áp thành phần | `U_R = I·R`, `U_L = I·X_L`, `U_C = I·X_C` | |
| Công suất thực | `P = U·I·cosφ = I²·R` | |
| Hệ số công suất | `cosφ = R / Z` | |
| Công suất biểu kiến | `S = U·I` | VA |
| Công suất phản kháng | `Q = U·I·sinφ` | VAR |
| Cộng hưởng RLC | `X_L = X_C → Z = R (min)` | `f₀ = 1/(2π√(LC))` |
| Tần số cộng hưởng | `f₀ = 1/(2π√(LC))` | |
| Hiệu suất | `η = P_tải / P_nguồn × 100%` | |

> **Đặc điểm CH:** Bài toán đa dạng – từ tính tổng trở đơn giản đến phân tích mạch nhánh có R, L, C ghép song song/nối tiếp.

---

### 5.3 NL – Dao Động Điện Từ & Năng Lượng Mạch LC

| Đại lượng | Công thức | Ghi chú |
|-----------|-----------|---------|
| Năng lượng tụ điện | `W_C = ½·C·U²` | Joule |
| Năng lượng cuộn cảm | `W_L = ½·L·I²` | Joule |
| Tổng năng lượng dao động | `W = W_C + W_L = ½·C·U²_max = ½·L·I²_max` | Bảo toàn |
| Tần số góc dao động | `ω₀ = 1/√(LC)` | rad/s |
| Chu kỳ dao động | `T = 2π√(LC)` | giây |
| Tần số dao động | `f = 1/(2π√(LC))` | Hz |
| Điện tích cực đại | `Q_max = C·U_max` | Coulomb |
| Điện tích tức thời | `q = Q_max·cos(ω₀t)` | |
| Năng lượng điện = năng lượng từ | `½·C·u² = ½·L·i²` | |
| Độ tự cảm | `L = (μ₀·N²·A) / l` | |
| Điện dung tụ | `C = Q / U` | |

> **Đặc điểm NL:** Bài toán chuyển hóa năng lượng giữa tụ và cuộn, tính thông số mạch LC dao động.

---

### 5.4 TD – Tụ Điện Phẳng

| Đại lượng | Công thức | Ghi chú |
|-----------|-----------|---------|
| Điện dung tụ phẳng | `C = ε₀·ε·A / d` | ε₀ = 8.854×10⁻¹² F/m |
| Điện tích | `Q = C·U` | Coulomb |
| Năng lượng | `W = ½·C·U² = Q²/(2C) = QU/2` | Joule |
| Điện trường trong tụ | `E = U / d` | V/m |
| Điện dung khi đổi môi trường | `C' = ε·C₀` | ε là hằng số điện môi |
| Tụ nối tiếp | `1/C_eq = 1/C₁ + 1/C₂ + ...` | |
| Tụ song song | `C_eq = C₁ + C₂ + ...` | |
| Ghép tụ (cùng chiều) | `U = (Q₁+Q₂)/(C₁+C₂)` | Điện tích cộng lại |
| Ghép tụ (ngược chiều) | `U = (Q₁-Q₂)/(C₁+C₂)` | Điện tích trừ nhau |
| Tụ ngắt nguồn, thay d | `Q = const, C' = ε₀A/d'` → `U' = Q/C'` | Q không đổi |
| Tụ vẫn nối nguồn, thay d | `U = const, C' = ε₀A/d'` → `Q' = C'U` | U không đổi |

> **Đặc điểm TD:** Bài toán thực tế – từ tính điện dung đơn giản đến ghép tụ, thay môi trường điện môi, cắt/nối nguồn.

---

### 5.5 DDT – Từ Trường & Cảm Ứng Điện Từ

| Đại lượng | Công thức | Ghi chú |
|-----------|-----------|---------|
| Từ trường trong solenoid | `B = μ₀·n·I` | n = N/l [turns/m] |
| Số vòng dây / đơn vị chiều dài | `n = N / l` | |
| Từ thông | `Φ = B·A·cosθ` | Weber (Wb) |
| Độ tự cảm solenoid | `L = μ₀·N²·A / l` | Henry (H) |
| Suất điện động cảm ứng | `e = -dΦ/dt = -L·dI/dt` | |
| Suất điện động trung bình | `e_tb = -ΔΦ / Δt` | |
| Năng lượng từ trường | `W_L = ½·L·I²` | Joule |
| Mật độ năng lượng từ | `w = B² / (2μ₀)` | J/m³ |
| Lực Lorentz | `F = q·v·B·sinα` | |
| Lực từ lên dây dẫn | `F = B·I·l·sinα` | |

> **Đặc điểm DDT:** Solenoid là bài toán trung tâm. Nhiều bài tính B, Φ, L rồi tính W_L hoặc e.

---

### 5.6 THCB – Thực Hành & Sai Số Đo Lường

| Đại lượng | Công thức | Ghi chú |
|-----------|-----------|---------|
| Sai số tuyệt đối | `ΔX = |X_đo - X_thực|` | |
| Sai số tương đối | `δX = ΔX / X × 100%` | % |
| Sai số dụng cụ | Thường = ½ × ĐCNN | |
| Sai số của tổng/hiệu | `ΔZ = ΔX + ΔY` | Z = X ± Y |
| Sai số của tích/thương | `δZ = δX + δY` | Z = X·Y hoặc X/Y |
| Sai số của hàm mũ | `δZ = n·δX` | Z = Xⁿ |
| Điện trở đo từ U, I | `R = U/I`, `δR = δU + δI` | |
| Công suất | `P = V·I`, `δP = δV + δI` | |
| Cường độ dòng điện | `I = P / V` | |

> **Đặc điểm THCB:** Bài toán sai số đo lường với ampe kế, vôn kế, thước kẹp... Đáp án thường là `%` hoặc kép (giá trị + sai số).

---

### 5.7 DT – Điện Thế & Hiệu Điện Thế

| Đại lượng | Công thức | Ghi chú |
|-----------|-----------|---------|
| Điện thế điểm | `V = k·q / r` | Volt |
| Cường độ điện trường điểm | `E = k·|q| / r²` | |
| Quan hệ E và V | `E = -dV/dr` (dọc đường sức) | |
| Hiệu điện thế | `U_AB = V_A - V_B = E·d` | d là khoảng cách |
| Điểm có V = 0 | Giải phương trình `V₁ + V₂ = 0` | Đối với 2 điện tích |
| Điểm có E = 0 | Giải `E₁ = E₂` (ngược chiều) | |
| E giữa 2 bản tụ | `E = U / d` | V/m |
| Tỉ lệ E tại 2 điểm | `E_A/E_B = (r_B/r_A)²` | Trên cùng đường sức |

> **Đặc điểm DT:** Bài toán tìm điểm đặc biệt (V=0, E=0) và tính E, V theo hình học.

---

### 5.8 CHLT – Mạch AC Nâng Cao (Cộng Hưởng)

| Đại lượng | Công thức | Ghi chú |
|-----------|-----------|---------|
| Điều kiện cộng hưởng | `X_L = X_C` → `ω₀ = 1/√(LC)` | |
| Kiểm tra cộng hưởng | Tính `X_L` và `X_C` rồi so sánh | |
| Tổng trở tại cộng hưởng | `Z_min = R` | |
| I cực đại | `I_max = U / R` | Khi cộng hưởng |
| P cực đại | `P_max = U²/R` | Khi cộng hưởng |

> **Đặc điểm CHLT:** Chỉ 20 câu, tập trung vào xác định điều kiện và hệ quả của cộng hưởng.

---

## 6. Thống Kê Chất Lượng Dataset

| Chỉ tiêu | Giá trị |
|----------|---------|
| Tổng câu hỏi | 1,352 |
| Câu hỏi thiếu (question) | 0 |
| Câu hỏi thiếu CoT | 0 |
| Câu hỏi thiếu answer | 0 |
| Câu hỏi thiếu unit | 14 (1.04%) |
| ID trùng lặp | 0 |
| Đáp án dạng số | 1,081 / 1,352 (80%) |
| Đáp án dạng biểu thức | 271 / 1,352 (20%) |
| Số bước CoT trung bình | **4.90 bước/câu** |
| Số bước CoT tối thiểu | 2 bước |
| Số bước CoT tối đa | 13 bước |

### Độ dài câu hỏi theo mã

| Mã | Trung bình (chars) | Ngắn nhất | Dài nhất |
|----|:-----------------:|:---------:|:--------:|
| DT | 251 | 117 | 402 |
| LD | 231 | 86 | 400 |
| TD | 173 | 72 | 335 |
| CH | 148 | 36 | 493 |
| CHLT | 128 | 76 | 175 |
| NL | 128 | 45 | 265 |
| DDT | 112 | 31 | 194 |
| THCB | 114 | 77 | 187 |

---

## 7. Nhận Xét & Đánh Giá Phân Phối

### ✅ Điểm mạnh
1. **Đầy đủ Chain-of-Thought:** Tất cả 1,352 câu đều có CoT với trung bình ~5 bước suy luận.
2. **Không có ID trùng:** Định danh nhất quán.
3. **Đa dạng chủ đề:** Phủ đủ chương trình Điện học / Vật lý điện từ phổ thông – đại học.
4. **Phân phối hình học phong phú (LD):** Bài toán tam giác đều, vuông, vuông cân, đường trung trực...

### ⚠️ Điểm cần lưu ý
1. **Mất cân bằng lớp:** LD chiếm 29.4%, CHLT chỉ 1.5% → cần cân nhắc khi train model.
2. **14 câu thiếu đơn vị (unit):** Chủ yếu ở TD và DT – nên kiểm tra và bổ sung.
3. **DDT bắt đầu từ DDT131** (không có DDT001–DDT130) → có thể thiếu ~130 câu đầu của nhóm này.
4. **20% đáp án dạng biểu thức** (e.g., `E₁ = (3/4)E₂`, `-2√2·q`): Cần xử lý riêng khi đánh giá model.
5. **Một số đơn vị không đồng nhất:** `μF` vs `µF`, `—` vs `-` (cùng ý nghĩa "không đơn vị") → cần chuẩn hóa.

---

## 8. Các Phần Cần Bổ Sung / Kiểm Tra Thêm

> [!IMPORTANT]
> Những phần dưới đây **chưa được phân tích** và nên được bổ sung:

- [ ] **Phân tích ngữ nghĩa câu hỏi (NLP):** Phân loại bài toán theo dạng (tìm lực, tìm điện trường, tìm tần số, v.v.)
- [ ] **Kiểm tra đáp án nhất quán:** Một số đáp án dạng số có thể bị lỗi làm tròn (ví dụ: `06.04` thay vì `6.04`)
- [ ] **Phân tích độ khó:** Dựa trên số bước CoT, độ dài câu hỏi → phân cấp Easy/Medium/Hard
- [ ] **Kiểm tra 14 câu thiếu unit:** Liệt kê ID cụ thể và điền đơn vị thích hợp
- [ ] **Chuẩn hóa đơn vị:** Thống nhất `μF` = `µF`, `-` = `—`
- [ ] **Bổ sung DDT001–DDT130:** Kiểm tra xem có thiếu câu không
- [ ] **Phân tích phân bố hình học (LD):** Tam giác đều / vuông / vuông cân / đường thẳng chiếm tỉ lệ bao nhiêu

---

## 9. Hướng Dẫn Sử Dụng Dataset

```python
import pandas as pd

df = pd.read_csv('Physics_Problems_Text_Only.csv')

# Lọc theo mã chủ đề
df_LD = df[df['id'].str.startswith('LD')]   # Tĩnh điện
df_CH = df[df['id'].str.startswith('CH')]   # Mạch AC
df_NL = df[df['id'].str.startswith('NL')]   # Dao động LC
df_TD = df[df['id'].str.startswith('TD')]   # Tụ điện
df_DDT = df[df['id'].str.startswith('DDT')] # Từ trường
df_THCB = df[df['id'].str.startswith('THCB')] # Thực hành
df_DT = df[df['id'].str.startswith('DT')]   # Điện thế
df_CHLT = df[df['id'].str.startswith('CHLT')] # Cộng hưởng
```

---

*Phân tích được thực hiện tự động từ file CSV gốc. Mọi cập nhật nên được ghi chú ở đây.*
