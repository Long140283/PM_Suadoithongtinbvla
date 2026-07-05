"""
Hằng số dùng chung toàn ứng dụng.
Tập trung tất cả magic strings vào đây để dễ bảo trì.
"""

# --- Trạng thái phiếu (FormSubmission.status) ---
class SubmissionStatus:
    PENDING_FINANCE = 'pending_finance'
    PENDING_ADMIN   = 'pending_admin'
    APPROVED        = 'approved'
    REJECTED_FINANCE = 'rejected_by_finance'
    REJECTED_ADMIN   = 'rejected_by_admin'

    ALL_PENDING = [PENDING_FINANCE, PENDING_ADMIN]
    ALL_REJECTED = [REJECTED_FINANCE, REJECTED_ADMIN]

# --- Tên quyền ---
class Permissions:
    VIEW_PATIENT             = 'view_patient'
    EDIT_PATIENT             = 'edit_patient'
    CREATE_REQUEST           = 'create_request'
    APPROVE_REQUEST          = 'approve_request'
    ACCESS_ADMIN_DASHBOARD   = 'access_admin_dashboard'
    MANAGE_FORMS             = 'manage_forms'
    MANAGE_USERS             = 'manage_users'
    MANAGE_PERMISSIONS       = 'manage_permissions'
    VIEW_AUDIT_LOG           = 'view_audit_log'
    BYPASS_FINANCE           = 'bypass_financial_approval'
    ACCESS_STATS             = 'access_statistical_report'
    USE_SCREENSHOT_FULL      = 'use_screenshot_full'
    USE_SCREENSHOT_REGION    = 'use_screenshot_region'
    USE_SCREENSHOT_WINDOW    = 'use_screenshot_window'
    USE_CAMERA               = 'use_camera'           # legacy – giữ để tương thích
    USE_CAMERA_BROWSER       = 'use_camera_browser'   # chụp qua trình duyệt (getUserMedia)
    USE_CAMERA_WINDOWS       = 'use_camera_windows'   # chụp qua OpenCV / Windows native

    # Tên hiển thị tiếng Việt
    DISPLAY_NAMES = {
        VIEW_PATIENT:           'Xem bệnh nhân',
        EDIT_PATIENT:           'Chỉnh sửa bệnh nhân',
        CREATE_REQUEST:         'Tạo yêu cầu',
        APPROVE_REQUEST:        'Phê duyệt yêu cầu',
        ACCESS_ADMIN_DASHBOARD: 'Truy cập trang quản trị',
        MANAGE_FORMS:           'Quản lý biểu mẫu',
        MANAGE_USERS:           'Quản lý người dùng',
        MANAGE_PERMISSIONS:     'Quản lý quyền',
        VIEW_AUDIT_LOG:         'Xem nhật ký kiểm toán',
        BYPASS_FINANCE:         'Gửi thẳng cho admin (bỏ qua duyệt tài chính)',
        ACCESS_STATS:           'Truy cập báo cáo thống kê',
        USE_SCREENSHOT_FULL:    'Chụp toàn màn hình',
        USE_SCREENSHOT_REGION:  'Chụp theo vùng',
        USE_SCREENSHOT_WINDOW:  'Chụp theo tác vụ',
        USE_CAMERA:             'Chụp từ Camera (legacy)',
        USE_CAMERA_BROWSER:     'Chụp từ Camera (Trình duyệt)',
        USE_CAMERA_WINDOWS:     'Chụp từ Camera (Windows/OpenCV)',
    }


# --- Tên vai trò ---
class Roles:
    ADMIN   = 'admin'
    STAFF   = 'staff'
    FINANCE = 'finance'

# --- File upload ---
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'xls', 'docx'}

# --- Nhãn trường động dùng để nhận diện bệnh nhân ---
PATIENT_CODE_KEYWORDS  = ['mã bệnh nhân', 'mã bn', 'patient_code']
PATIENT_NAME_KEYWORDS  = ['họ và tên', 'tên bệnh nhân', 'patient_name']
DEPARTMENT_KEYWORDS    = ['khoa/phòng', 'khoa', 'phòng']
