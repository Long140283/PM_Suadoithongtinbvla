from datetime import datetime, timedelta
from flask import url_for, current_app
from flask_login import current_user
from .models import DynamicForm, FormSubmission
from .constants import SubmissionStatus, Roles

def inject_dynamic_forms():
    from .utils import get_server_info
    server_info = get_server_info()
    data = {
        'dynamic_forms': DynamicForm.query.with_entities(DynamicForm.id, DynamicForm.name).all(),
        'notifications': [],
        # Thong tin server hien thi tren giao dien (Tu dong cap nhat)
        'server_hostname': server_info['hostname'],
        'server_local_ip': server_info['local_ip'],
        'server_all_ips':  server_info['all_ips'],
        'server_port':     server_info['port'],
    }
    
    if current_user.is_authenticated:
        # 1. Finance sees all PENDING_FINANCE
        if current_user.has_role(Roles.FINANCE):
            subs = FormSubmission.query.filter_by(status=SubmissionStatus.PENDING_FINANCE).all()
            for s in subs:
                data['notifications'].append({
                    'message': f"Yêu cầu mới từ {s.user.full_name if s.user else 'N/A'}",
                    'timestamp': s.submitted_at,
                    'url': url_for('patient.show_dynamic_form_submission', submission_id=s.id)
                })
        
        # 2. Admin sees all PENDING_ADMIN
        elif current_user.is_admin():
            subs = FormSubmission.query.filter_by(status=SubmissionStatus.PENDING_ADMIN).all()
            for s in subs:
                data['notifications'].append({
                    'message': f"Yêu cầu chờ duyệt: {s.form.name if s.form else 'Phiếu'}",
                    'timestamp': s.submitted_at,
                    'url': url_for('patient.show_dynamic_form_submission', submission_id=s.id)
                })
        
        # 3. Staff sees recent updates (last 24 hours) to their requests
        else:
            since = datetime.utcnow() - timedelta(hours=24)
            if current_user.last_notification_read:
                since = max(since, current_user.last_notification_read)
                
            subs = FormSubmission.query.filter(
                FormSubmission.user_id == current_user.id,
                FormSubmission.status.in_([SubmissionStatus.APPROVED] + SubmissionStatus.ALL_REJECTED),
                FormSubmission.updated_at > since
            ).all()
            for s in subs:
                status_text = "đã được duyệt" if s.status == SubmissionStatus.APPROVED else "bị từ chối"
                data['notifications'].append({
                    'message': f"Phiếu #{s.id} {status_text}",
                    'timestamp': s.updated_at,
                    'url': url_for('patient.show_dynamic_form_submission', submission_id=s.id)
                })
    
    return data