from datetime import datetime, timedelta
from flask import url_for
from flask_login import current_user
from .models import DynamicForm, FormSubmission
from .constants import SubmissionStatus, Roles

def inject_dynamic_forms():
    data = {
        'dynamic_forms': DynamicForm.query.with_entities(DynamicForm.id, DynamicForm.name).all(),
        'notifications': []
    }
    
    if current_user.is_authenticated:
        # 1. Finance sees all PENDING_FINANCE
        if current_user.has_role(Roles.FINANCE):
            subs = FormSubmission.query.filter_by(status=SubmissionStatus.PENDING_FINANCE).all()
            for s in subs:
                data['notifications'].append({
                    'message': f"Yêu cầu mới từ {s.user.full_name if s.user else 'N/A'}",
                    'timestamp': s.submitted_at,
                    'url': url_for('patient.finance_dashboard')
                })
        
        # 2. Admin sees all PENDING_ADMIN
        elif current_user.is_admin():
            subs = FormSubmission.query.filter_by(status=SubmissionStatus.PENDING_ADMIN).all()
            for s in subs:
                data['notifications'].append({
                    'message': f"Yêu cầu chờ duyệt: {s.form.name if s.form else 'Phiếu'}",
                    'timestamp': s.submitted_at,
                    'url': url_for('admin.dashboard')
                })
        
        # 3. Staff sees recent updates (last 24 hours) to their requests
        else:
            since = datetime.utcnow() - timedelta(hours=24)
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
                    'url': url_for('patient.staff_dashboard')
                })
    
    return data