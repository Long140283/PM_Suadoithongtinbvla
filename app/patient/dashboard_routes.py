"""
Dashboard routes cho staff va finance.
Tach ra khoi routes.py chinh de de bao tri.
"""
import logging
from datetime import datetime, date

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import FormSubmission, User, Patient, Attachment, AuditLog
from app.constants import SubmissionStatus, Roles
from app.decorators import role_required
from app.utils import enrich_submissions
from app.patient.forms import EmptyForm, RejectionForm

from . import patient_bp

logger = logging.getLogger(__name__)


def _parse_date(date_str, fmt='%Y-%m-%d'):
    try:
        return datetime.strptime(date_str, fmt).date()
    except (ValueError, TypeError):
        return date.today()


# ---------------------------------------------------------------------------
# Staff dashboard
# ---------------------------------------------------------------------------

@patient_bp.route('/staff_dashboard')
@login_required
def staff_dashboard():
    selected_date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    show_all = request.args.get('show_all', 'false').lower() == 'true'
    selected_date = _parse_date(selected_date_str)

    start_of_day = datetime.combine(selected_date, datetime.min.time())
    end_of_day   = datetime.combine(selected_date, datetime.max.time())

    # Base query for the selected date
    base_query = FormSubmission.query.filter(
        FormSubmission.submitted_at >= start_of_day,
        FormSubmission.submitted_at <= end_of_day,
    )

    # Apply role-based filtering (Staff only see their department)
    is_privileged = current_user.is_admin() or current_user.is_finance
    if not is_privileged:
        if current_user.department_id:
            base_query = base_query.join(User, FormSubmission.user_id == User.id)\
                                   .filter(User.department_id == current_user.department_id)
        else:
            base_query = base_query.filter(FormSubmission.user_id == current_user.id)

    # 1. Main request list
    if show_all:
        display = base_query.all()
    else:
        display = base_query.filter(
            FormSubmission.status.in_(SubmissionStatus.ALL_PENDING + SubmissionStatus.ALL_REJECTED)
        ).all()

    display = sorted(enrich_submissions(display), key=lambda s: s.submitted_at, reverse=True)

    # 2. Statistics (using the SAME base_query)
    total_today    = base_query.count()
    approved_today = base_query.filter(FormSubmission.status == SubmissionStatus.APPROVED).count()
    pending_today  = total_today - approved_today

    logger.debug(f"Dashboard Stats for {current_user.username}: total={total_today}, approved={approved_today}, pending={pending_today}")

    return render_template(
        'staff_dashboard.html',
        all_requests=display,
        form=EmptyForm(),
        patients_created_today=total_today,
        approved_patients_today=approved_today,
        pending_patients_today=pending_today,
        selected_date=selected_date.strftime('%d-%m-%Y'),
        today=date.today().strftime('%Y-%m-%d'),
    )


# ---------------------------------------------------------------------------
# Finance dashboard
# ---------------------------------------------------------------------------

@patient_bp.route('/finance_dashboard')
@login_required
@role_required(Roles.FINANCE, Roles.ADMIN)
def finance_dashboard():
    show_all = request.args.get('show_all', 'false').lower() == 'true'
    selected_date_str = request.args.get('date', date.today().strftime('%d/%m/%Y'))

    if show_all:
        pending = FormSubmission.query.filter_by(
            status=SubmissionStatus.PENDING_FINANCE
        ).order_by(FormSubmission.submitted_at.desc()).all()
        selected_date_str = ''
    else:
        selected_date = _parse_date(selected_date_str, '%d/%m/%Y')
        start = datetime.combine(selected_date, datetime.min.time())
        end   = datetime.combine(selected_date, datetime.max.time())
        pending = FormSubmission.query.filter(
            FormSubmission.status == SubmissionStatus.PENDING_FINANCE,
            FormSubmission.submitted_at >= start,
            FormSubmission.submitted_at <= end,
        ).order_by(FormSubmission.submitted_at.desc()).all()

    rejected = FormSubmission.query.filter_by(
        status=SubmissionStatus.REJECTED_FINANCE
    ).order_by(FormSubmission.submitted_at.desc()).all()

    return render_template(
        'finance_dashboard.html',
        pending_requests=enrich_submissions(pending),
        rejected_requests=enrich_submissions(rejected),
        form=EmptyForm(),
        rejection_form=RejectionForm(),
        selected_date_str=selected_date_str,
    )


# ---------------------------------------------------------------------------
# Finance: duyet / tu choi
# ---------------------------------------------------------------------------

@patient_bp.route('/finance/approve/<int:submission_id>', methods=['POST'])
@login_required
@role_required(Roles.FINANCE, Roles.ADMIN)
def finance_approve(submission_id):
    sub = FormSubmission.query.get_or_404(submission_id)
    if sub.status != SubmissionStatus.PENDING_FINANCE:
        flash('Yeu cau khong o trang thai cho xu ly.', 'warning')
        return redirect(url_for('patient.finance_dashboard'))

    sub.status = SubmissionStatus.PENDING_ADMIN
    db.session.add(AuditLog(
        user_id=current_user.id,
        action='finance_approved',
        details=f'Finance approved submission {sub.id}',
    ))
    db.session.commit()
    flash('Da chuyen phieu cho admin duyet.', 'success')
    return _smart_redirect('patient.finance_dashboard')


@patient_bp.route('/finance/reject/<int:submission_id>', methods=['POST'])
@login_required
@role_required(Roles.FINANCE, Roles.ADMIN)
def finance_reject(submission_id):
    sub = FormSubmission.query.get_or_404(submission_id)
    if sub.status != SubmissionStatus.PENDING_FINANCE:
        flash('Yeu cau khong o trang thai cho xu ly.', 'warning')
        return redirect(url_for('patient.finance_dashboard'))

    form = RejectionForm()
    if form.validate_on_submit():
        sub.status = SubmissionStatus.REJECTED_FINANCE
        sub.rejection_reason = form.reason.data
        db.session.add(AuditLog(
            user_id=current_user.id,
            action='finance_rejected',
            details=f'Finance rejected submission {sub.id}: {form.reason.data}',
        ))
        db.session.commit()
        flash('Da tu choi phieu.', 'success')
    else:
        for errors in form.errors.values():
            for e in errors:
                flash(e, 'danger')
    return _smart_redirect('patient.finance_dashboard')


# ---------------------------------------------------------------------------
# API polling (long-polling nhe cho JS)
# ---------------------------------------------------------------------------

@patient_bp.route('/api/finance/pending')
@login_required
@role_required(Roles.FINANCE, Roles.ADMIN)
def api_finance_pending():
    since_id = request.args.get('since_id', 0, type=int)
    subs = FormSubmission.query.filter(
        FormSubmission.status == SubmissionStatus.PENDING_FINANCE,
        FormSubmission.id > since_id,
    ).order_by(FormSubmission.id.asc()).all()

    from app.utils import extract_patient_info
    data = []
    for s in subs:
        info = extract_patient_info(s)
        user = User.query.get(s.user_id)
        data.append({
            'id': s.id,
            'form_name': s.form.name if s.form else 'N/A',
            'patient_code': info['code'],
            'patient_name': info['name'],
            'requester_name': user.full_name if user else 'N/A',
            'formatted_date': s.submitted_at.strftime('%d/%m %H:%M') if s.submitted_at else '',
        })
    return jsonify({'requests': data})


@patient_bp.route('/api/staff/notifications')
@login_required
def api_staff_notifications():
    from datetime import timedelta
    since_str = request.args.get('since_time')
    try:
        if since_str:
            since_str = since_str.rstrip('Z')
            since = datetime.fromisoformat(since_str)
        else:
            since = datetime.utcnow() - timedelta(minutes=5)
    except ValueError:
        since = datetime.utcnow() - timedelta(minutes=5)

    subs = FormSubmission.query.filter(
        FormSubmission.user_id == current_user.id,
        FormSubmission.updated_at > since,
    ).all()

    from app.utils import extract_patient_info
    notifications = []
    for s in subs:
        info = extract_patient_info(s)
        notifications.append({
            'id': s.id,
            'status': s.status,
            'patient_name': info['name'],
            'updated_at': s.updated_at.isoformat(),
        })
    return jsonify({'notifications': notifications, 'server_time': datetime.utcnow().isoformat()})


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _smart_redirect(fallback_endpoint):
    """Redirect ve trang truoc neu co, nguoc lai dung fallback."""
    if request.referrer and 'dashboard' in request.referrer:
        return redirect(request.referrer)
    return redirect(url_for(fallback_endpoint))
