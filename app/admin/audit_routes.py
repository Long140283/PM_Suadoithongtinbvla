from flask import render_template, request
from flask_login import login_required
from datetime import datetime

from . import admin
from ..models import AuditLog, User
from ..decorators import permission_required
from ..constants import Permissions


@admin.route('/audit')
@login_required
@permission_required(Permissions.VIEW_AUDIT_LOG)
def audit():
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Or any other number of items per page

    query = AuditLog.query

    # Search parameters
    user_name = request.args.get('user_name')
    action_type = request.args.get('action_type')
    search_details = request.args.get('search_details')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if user_name:
        # Assuming AuditLog has a user relationship to a User model with a username
        query = query.join(User).filter(User.username.ilike(f'%{user_name}%'))

    if action_type:
        query = query.filter(AuditLog.action.ilike(f'%{action_type}%'))

    if search_details:
        # Searching for patient name or other details in the details field
        query = query.filter(AuditLog.details.ilike(f'%{search_details}%'))

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        query = query.filter(AuditLog.timestamp >= start_date)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        query = query.filter(AuditLog.timestamp <= end_date)

    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items

    return render_template('admin/audit.html', logs=logs, pagination=pagination)