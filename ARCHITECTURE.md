# Kiến Trúc Hệ Thống (Architecture & Modules)

Tài liệu này mô tả cấu trúc và các module hiện tại của phần mềm `PM_SuaDoiThongTin` (Patient App) nhằm hỗ trợ việc bảo trì và phát triển tiếp theo.

## Tổng Quan

- **Ngôn ngữ/Framework:** Python 3, Flask
- **Cơ sở dữ liệu:** SQLite (có thể cấu hình sang PostgreSQL/MySQL thông qua SQLAlchemy)
- **Giao diện (Frontend):** Jinja2 Templates, Bootstrap 5, FontAwesome
- **Thư viện chính:** Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, openpyxl (xuất báo cáo)

## Cấu Trúc Các Module (Blueprints)

Hệ thống được chia nhỏ thành các Blueprint để dễ quản lý:

### 1. `auth` (Xác thực)
- Đăng nhập, đăng xuất.
- Đăng ký tài khoản (dành cho Admin).

### 2. `admin` (Quản trị viên)
- Bảng điều khiển (Dashboard).
- Quản lý người dùng, phân quyền.
- Quản lý biểu mẫu (Dynamic Forms).
- Nhật ký hệ thống (Audit Logs).

### 3. `patient` (Nghiệp vụ Bệnh nhân & Y bác sĩ)
- Đón tiếp, tạo hồ sơ bệnh nhân.
- Tạo và quản lý các phiếu thông tin động (`DynamicFormSubmission`) cho bệnh nhân.
- Phê duyệt phiếu (Dành cho cấp quản lý).

### 4. `activity_report` (Báo cáo hoạt động)
- Báo cáo số liệu tổng hợp các phiếu đã nộp, phân loại theo khoa phòng và trạng thái.

### 5. `patient_search` (Tìm kiếm phiếu / Tra cứu bệnh nhân)
- *Thêm mới gần đây:* Cung cấp giao diện tra cứu nâng cao.
- Có khả năng lọc bệnh nhân theo Mã BN, Mã BHYT, SĐT, Họ Tên (có tuỳ chọn "Tìm đúng" - khớp chính xác hoặc gần đúng).
- Lọc theo khoảng thời gian, trạng thái phiếu và khoa phòng.

### 6. `report_search` (Báo cáo tra cứu & Kết xuất)
- *Thêm mới gần đây:* Giao diện dạng form Full-width để xuất dữ liệu.
- Cho phép người dùng lọc dữ liệu tương tự `patient_search` nhưng tập trung vào việc **Kết xuất dữ liệu**.
- Nút "XEM BÁO CÁO" dạng Dropdown cho phép xuất file trực tiếp (hiện đã hỗ trợ kết xuất ra định dạng Excel `.xlsx` sử dụng thư viện `openpyxl`).

### 7. `screenshot_bp` & `static_bp`
- Các tiện ích hỗ trợ lưu trữ hình ảnh và phục vụ file tĩnh.

## Cấu Trúc Thư Mục

```text
PM_SuaDoiThongTin/
├── app/
│   ├── activity_report/    # Báo cáo hoạt động
│   ├── admin/              # Module Quản trị
│   ├── auth/               # Module Xác thực
│   ├── patient/            # Module Bệnh nhân
│   ├── patient_search/     # Tra cứu hồ sơ/phiếu (mới)
│   ├── report_search/      # Kết xuất báo cáo (mới)
│   ├── static/             # CSS, JS, Images
│   ├── templates/          # HTML Templates (có base.html dùng chung)
│   ├── models.py           # Định nghĩa CSDL (SQLAlchemy)
│   └── __init__.py         # Khởi tạo App & Blueprints
├── migrations/             # Thư mục chứa các bản DB migrations
├── config.py               # Cấu hình môi trường
├── requirements.txt        # Các thư viện phụ thuộc
├── run.py                  # Script chạy môi trường Dev
├── setup_nssm_service.bat  # Cài đặt ứng dụng như Windows Service
└── ARCHITECTURE.md         # File tài liệu này
```

## Các Lưu Ý Khi Phát Triển Tiếp
- **Bổ sung trường CSDL:** Nếu khách hàng yêu cầu thêm các trường như `Mã BA` (Bệnh án), `Mã LK` (Lượt khám), `CCCD` vào chức năng tìm kiếm, cần thêm các cột tương ứng vào Model `Patient` trong `app/models.py`, sau đó chạy `flask db migrate` và `flask db upgrade`.
- **Giao diện:** Toàn bộ giao diện hiện tại ưu tiên sử dụng Bootstrap grid và components (`card`, `row`, `col`) để đảm bảo tính đồng bộ (`base.html`). Khi tạo trang mới, nên kế thừa `base.html` và thiết lập `{% block container_class %}container-fluid{% endblock %}` nếu cần layout full màn hình.
- **Tính năng xuất báo cáo:** Hiện tại logic xuất Excel được viết trong `app/report_search/routes.py`. Nếu có thêm định dạng (RTF, PDF), có thể bổ sung các thư viện tương ứng và xử lý tại Route đó.
