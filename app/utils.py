"""
Hàm tiện ích dùng chung toàn ứng dụng.
Tập trung logic lặp lại để tránh code trùng.
"""
import os
import logging
import socket
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

import time

_server_info_cache = {
    'data': None,
    'expiry': 0
}

def get_server_info(force_refresh=False):
    """
    Tự động xác định tất cả IP LAN, Hostname và Port của máy chủ.
    Hỗ trợ máy tính có nhiều card mạng (Ethernet, Wifi, VirtualBox...).
    """
    global _server_info_cache
    now = time.time()
    
    if not force_refresh and _server_info_cache['data'] and now < _server_info_cache['expiry']:
        return _server_info_cache['data']

    # 1. Hostname
    hostname = socket.gethostname()
    
    # 2. Port
    port = int(os.environ.get('PORT', 8001))
    
    # 3. Thu thập tất cả các IP khả dụng
    all_ips = set()
    primary_ip = '127.0.0.1'

    # Cách A: Thử kết nối UDP để tìm IP "chính" (interface có internet)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # 8.8.8.8 là DNS Google, dùng để OS chọn interface có thể ra ngoài
        s.connect(('8.8.8.8', 80))
        primary_ip = s.getsockname()[0]
        all_ips.add(primary_ip)
        s.close()
    except Exception:
        pass

    # Cách B: Dùng gethostbyname_ex để lấy danh sách IP từ hostname
    try:
        _, _, ip_list = socket.gethostbyname_ex(hostname)
        for ip in ip_list:
            if not ip.startswith('127.'):
                all_ips.add(ip)
    except Exception:
        pass

    # Cách C: Dùng getaddrinfo (Duyệt qua các interface)
    try:
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith('127.') and not ip.startswith('169.254.'):
                all_ips.add(ip)
    except Exception:
        pass

    # Chuyển thành list và sắp xếp
    sorted_ips = sorted(list(all_ips))
    
    # Nếu không tìm thấy IP nào ngoài loopback
    if not sorted_ips:
        sorted_ips = [primary_ip] if primary_ip != '127.0.0.1' else ['127.0.0.1']
    
    # Đảm bảo primary_ip luôn ở đầu danh sách nếu nó hợp lệ
    if primary_ip in sorted_ips:
        sorted_ips.remove(primary_ip)
        sorted_ips.insert(0, primary_ip)

    server_info = {
        'hostname': hostname,
        'local_ip': sorted_ips[0], # IP ưu tiên nhất
        'all_ips':  sorted_ips,    # Danh sách tất cả IP
        'port':     port
    }
    
    # Cache kết quả trong 60 giây
    _server_info_cache['data'] = server_info
    _server_info_cache['expiry'] = now + 60
    
    return server_info
