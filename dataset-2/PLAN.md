# Tạo `physic_version_2.csv` Cho Dataset Physics

## Summary
- Source đã kiểm tra: 1352 câu, topic counts khớp repo: THCB 80, CH 290, LD 397, TD 177, DT 68, NL 190, DDT 130, CHLT 20.
- Con số “474” không hoàn toàn nhất quán: bảng topic cộng lại là 478. Audit nghiêm hơn còn có thể ra nhiều hơn, nên không dùng số 474 làm target cứng.
- Việc LoRA kém hơn base chưa đủ kết luận là catastrophic forgetting. Ví dụ `DDT131` trong dataset có CoT tốt nhưng LoRA vẫn chọn sai công thức, nên nguyên nhân còn gồm CoT nhiễu/ngắn, format SFT, retrieval/solver, unit conversion và evaluator.

## Data Interface
- Tạo file mới: `dataset_2/physic_version_2.csv`.
- Giữ nguyên schema, thứ tự dòng và các cột: `id,question,cot,answer,unit`.
- Chỉ sửa cột `cot`; không sửa `question`, `answer`, `unit`.
- Không overwrite `dataset_2/Physics_Problems_Text_Only.csv`.
- Chọn câu cần sửa bằng audit chọn lọc:
  - `no_calculations`: bài định lượng nhưng CoT thiếu thay số, phép tính trung gian, hoặc bước ra đáp án.
  - `vague_steps`: chỉ nói “identify/recall/calculate/substitute” nhưng không giải thật.
  - `missing_geo_step`: bài có hình học/vector nhưng thiếu phân tích khoảng cách, góc, phương, thành phần, đối xứng.
  - `too_short`: CoT quá ngắn hoặc bị lỗi ghép/lặp câu như `THCB001`.

## Topic Rewrite Plan
- THCB: ưu tiên sửa gần toàn bộ các câu lỗi đo lường, làm rõ least count, absolute error, relative error, percentage error, average/random error; dọn các CoT bị lặp/ghép câu.
- LD: thêm bước hình học trước Coulomb: đổi cm sang m, xác định tam giác/collinear/perpendicular bisector, tính từng lực/trường, phân tích hướng và hợp lực vector.
- DT: tách rõ điện thế là đại lượng vô hướng, điện trường/lực là vector; sửa các câu zero-field/zero-potential, midpoint, perpendicular bisector, field-first rồi mới tính lực lên `q3`.
- TD: bổ sung phép đổi đơn vị `μF`, `mC`, `cm`, các công thức `C = Q/U`, `W = 0.5CU^2`, `E = U/d`, và trạng thái capacitor connected/disconnected.
- CH: bổ sung tính trung gian cho RLC AC: `X_L`, `X_C`, `Z`, `I`, `P`, `cosφ`, resonance; tránh chỉ nêu công thức mà không tính.
- NL: làm rõ bảo toàn năng lượng LC, chuyển đổi giữa năng lượng tụ/cuộn cảm, thời điểm năng lượng bằng nhau, và công thức tần số/chu kỳ.
- DDT: chỉ sửa các câu thật sự mỏng; không rewrite các câu đã tốt như `DDT131`. Nhấn mạnh phân biệt `B`, `Φ`, `NΦ`, `L`, `u = B^2/(2μ0)`, EMF định lượng và câu định tính.
- CHLT: sửa ít, tập trung resonance yes/no, `f0`, `Q`, bandwidth, và điều kiện cộng hưởng.

## Validation And Tests
- Parse lại CSV mới bằng `csv.DictReader`; assert đúng 1352 rows và topic counts không đổi.
- So sánh file gốc và file mới; assert chỉ cột `cot` được thay đổi.
- Với mỗi CoT được rewrite, assert có `Step 1...`, không rỗng, không lặp câu lỗi, và final step khớp `answer + unit` hiện có.
- Spot-check bắt buộc: `THCB001`, `LD001`, `LD002`, `DT004`, `DT025`, `DDT139`, `DDT141`, `TD401`, `CH007`, `NL001`, `CHLT009`.
- Regenerate SFT bằng CSV mới, ví dụ `python finetuning/scripts/prepare_sft_dataset.py --dataset dataset_2/physic_version_2.csv --output finetuning/data/processed_v2`.
- Chạy regression tests: `python -m unittest tests/test_finetuning_data_prep.py tests/test_hint_engine.py`.

## Assumptions
- Output path mặc định là `dataset_2/physic_version_2.csv`, theo tên bạn yêu cầu.
- Nếu audit phát hiện `answer/unit` có vẻ sai, vẫn không sửa nhãn trong file v2; ghi nhận ID trong báo cáo cuối sau khi thực hiện.
- Mục tiêu của v2 là cải thiện chất lượng supervised CoT cho fine-tuning, không thay thế solver/RAG. Với DT/LD/DDT, muốn tăng mạnh accuracy vẫn nên bổ sung deterministic geometry/formula guard sau bước dataset này.
