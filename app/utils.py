"""
Hàm tiện ích dùng chung toàn ứng dụng.
Tập trung logic lặp lại để tránh code trùng.
"""
import os
import logging
from flask import current_app
from werkzeug.utils import secure_filename
from .constants import ALLOWED_EXTENSIONS, PATIENT_CODE_KEYWORDS, PATIENT_NAME_KEYWORDS

logger = logging.getLogger(__name__)


def allowed_file(filename: str) -> bool:
    """Kiểm tra phần mở rộng file có được phép không."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file, subfolder: str = 'dynamic_forms') -> str | None:
    """
    Lưu file upload vào thư mục cấu hình.
    Trả về đường dẫn tuyệt đối hoặc None nếu thất bại.
    """
    if not file or not allowed_file(file.filename):
        return None
    filename = secure_filename(file.filename)
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    return file_path


def extract_patient_info(submission) -> dict:
    """
    Trích xuất thông tin bệnh nhân từ SubmissionValue.
    Ưu tiên dùng quan hệ submission.patient nếu có.
    Trả về dict: {'code': ..., 'name': ..., 'department': ...}
    """
    if submission.patient:
        dept = submission.patient.department.name if submission.patient.department else 'N/A'
        return {
            'code': submission.patient.patient_code,
            'name': submission.patient.full_name,
            'department': dept,
        }

    code = name = department = None
    for v in submission.values:
        label = v.field.label.lower()
        if code is None and any(k in label for k in PATIENT_CODE_KEYWORDS):
            code = v.value
        if name is None and any(k in label for k in PATIENT_NAME_KEYWORDS):
            name = v.value
        if department is None and ('khoa' in label or 'phòng' in label):
            department = v.value

    # Nếu có mã BN, thử tra cứu trong DB
    if code:
        from .models import Patient
        patient = Patient.query.filter_by(patient_code=code).first()
        if patient:
            name = patient.full_name
            department = patient.department.name if patient.department else department

    return {
        'code': code,
        'name': name or 'N/A',
        'department': department or 'N/A',
    }


def enrich_submissions(submissions: list) -> list:
    """
    Gắn thêm thông tin patient_code, patient_name, requester_name,
    has_attachments vào mỗi submission để template dùng trực tiếp.
    """
    from .models import Attachment, User
    for sub in submissions:
        info = extract_patient_info(sub)
        sub.patient_code_display = info['code']
        sub.patient_name_display = info['name']
        sub.department_display   = info['department']

        user = User.query.get(sub.user_id)
        sub.requester_name_display = user.full_name if user else 'N/A'

        sub.attachments_list = Attachment.query.filter_by(form_submission_id=sub.id).all()
        sub.has_attachments = bool(sub.attachments_list)
    return submissions
