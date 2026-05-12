"""
Admin routes: dashboard, quan ly bieu mau dong, duyet/tu choi phieu.
"""
import logging
from datetime import datetime, date

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (DynamicForm, FormField, FormSubmission,
                        SubmissionValue, Attachment, AuditLog, Patient)
from app.admin.forms import DynamicFormForm, FormFieldForm, DeleteForm
from app.patient.forms import RejectionForm
from app.decorators import permission_required, role_required
from app.constants import SubmissionStatus, Permissions, Roles
from app.utils import extract_patient_info, enrich_submissions

from . import admin

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@admin.route('/dashboard')
@login_required
@permission_required(Permissions.ACCESS_ADMIN_DASHBOARD)
def dashboard():
    show_all = request.args.get('show_all') == 'true'
    selected_date_str = request.args.get('selected_date', date.today().strftime('%Y-%m-%d'))

    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = date.today()
        selected_date_str = selected_date.strftime('%Y-%m-%d')

    query = FormSubmission.query
    
    if show_all:
        # Fetch all pending requests across all dates
        query = query.filter(FormSubmission.status == SubmissionStatus.PENDING_ADMIN)
    else:
        # Fetch all requests (all statuses) for the selected date so tabs work
        query = query.filter(db.func.date(FormSubmission.submitted_at) == selected_date)

    submissions = query.all()
    all_requests = []
    for sub in submissions:
        info = extract_patient_info(sub)
        all_requests.append({
            'id':             sub.id,
            'type':           'dynamic_form',
            'patient_code':   info['code'],
            'patient_name':   info['name'],
            'department':     info['department'],
            'requester_name': sub.user.full_name if sub.user else 'N/A',
            'request_date':   sub.submitted_at,
            'status':         sub.status,
            'has_attachments': bool(sub.attachments),
            'raw_request':    sub,
        })

    all_requests.sort(key=lambda r: r['request_date'], reverse=True)
    return render_template(
        'admin/dashboard.html',
        all_requests=all_requests,
        selected_date=selected_date_str,
        rejection_form=RejectionForm(),
    )


# ---------------------------------------------------------------------------
# API polling cho admin
# ---------------------------------------------------------------------------

@admin.route('/api/admin/pending')
@login_required
@role_required(Roles.ADMIN)
def api_admin_pending():
    since_id = request.args.get('since_id', 0, type=int)
    subs = FormSubmission.query.filter(
        FormSubmission.status == SubmissionStatus.PENDING_ADMIN,
        FormSubmission.id > since_id,
    ).order_by(FormSubmission.id.asc()).all()

    data = []
    for sub in subs:
        info = extract_patient_info(sub)
        data.append({
            'id':             sub.id,
            'type':           'dynamic_form',
            'patient_code':   info['code'],
            'patient_name':   info['name'],
            'department':     info['department'],
            'requester_name': sub.user.full_name if sub.user else 'N/A',
            'formatted_date': sub.submitted_at.strftime('%d/%m %H:%M') if sub.submitted_at else '',
            'view_url':       url_for('patient.show_dynamic_form_submission', submission_id=sub.id),
        })
    return jsonify({'requests': data})


# ---------------------------------------------------------------------------
# Duyet / Tu choi phieu (admin)
# ---------------------------------------------------------------------------

@admin.route('/approve/<request_type>/<int:id>', methods=['POST'])
@login_required
@permission_required(Permissions.MANAGE_FORMS)
@role_required(Roles.ADMIN)
def approve_request(id, request_type):
    if request_type != 'dynamic_form':
        flash('Loai yeu cau khong hop le.', 'danger')
        return redirect(url_for('admin.dashboard'))

    sub = FormSubmission.query.get_or_404(id)
    if sub.status != SubmissionStatus.PENDING_ADMIN:
        flash('Yeu cau khong o trang thai cho xu ly.', 'warning')
        return redirect(url_for('admin.dashboard'))

    sub.status = SubmissionStatus.APPROVED
    sub.approved_by_id = current_user.id
    db.session.add(AuditLog(
        user_id=current_user.id,
        action='admin_approved',
        details=f'Admin approved submission {sub.id}',
    ))
    db.session.commit()
    flash('Yeu cau da duoc phe duyet.', 'success')
    return _smart_redirect('admin.dashboard')


@admin.route('/reject_request/<int:id>/<request_type>', methods=['POST'])
@login_required
@permission_required(Permissions.MANAGE_FORMS)
@role_required(Roles.ADMIN)
def reject_request(id, request_type):
    if request_type != 'dynamic_form':
        flash('Loai yeu cau khong hop le.', 'danger')
        return redirect(url_for('admin.dashboard'))

    sub = FormSubmission.query.get_or_404(id)
    if sub.status != SubmissionStatus.PENDING_ADMIN:
        flash('Yeu cau khong o trang thai cho xu ly.', 'warning')
        return redirect(url_for('admin.dashboard'))

    form = RejectionForm()
    if form.validate_on_submit():
        sub.status = SubmissionStatus.REJECTED_ADMIN
        sub.rejection_reason = form.reason.data
        db.session.add(AuditLog(
            user_id=current_user.id,
            action='admin_rejected',
            details=f'Admin rejected submission {sub.id}: {form.reason.data}',
        ))
        db.session.commit()
        flash('Yeu cau da bi tu choi.', 'success')
    else:
        for errors in form.errors.values():
            for e in errors:
                flash(e, 'danger')
    return _smart_redirect('admin.dashboard')


# ---------------------------------------------------------------------------
# Quan ly bieu mau dong (admin)
# ---------------------------------------------------------------------------

@admin.route('/forms')
@login_required
@permission_required(Permissions.MANAGE_FORMS)
def manage_forms_list():
    forms = DynamicForm.query.all()
    for f in forms:
        f.fields_count = f.fields.count()
    return render_template('admin/forms.html', forms=forms)


@admin.route('/forms/create', methods=['GET', 'POST'])
@login_required
@permission_required(Permissions.MANAGE_FORMS)
def create_form():
    form = DynamicFormForm()
    form.copy_from.choices = [('0', 'Khong')] + [(f.id, f.name) for f in DynamicForm.query.all()]

    if form.validate_on_submit():
        if DynamicForm.query.filter_by(name=form.name.data).first():
            flash('Bieu mau voi ten nay da ton tai.', 'danger')
            return render_template('admin/form_create.html', form=form)

        new_form = DynamicForm(
            name=form.name.data,
            description=form.description.data,
            user_id=current_user.id,
        )
        db.session.add(new_form)
        db.session.flush()

        if form.copy_from.data and form.copy_from.data != '0':
            source = DynamicForm.query.get(int(form.copy_from.data))
            if source:
                for field in source.fields:
                    db.session.add(FormField(
                        label=field.label,
                        field_type=field.field_type,
                        options=field.options,
                        required=field.required,
                        order=field.order,
                        form_id=new_form.id,
                    ))

        db.session.commit()
        flash('Bieu mau da duoc tao.', 'success')
        return redirect(url_for('admin.manage_forms_list'))

    return render_template('admin/form_create.html', form=form)


@admin.route('/forms/edit/<int:form_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permissions.MANAGE_FORMS)
def edit_form(form_id):
    d_form = DynamicForm.query.get_or_404(form_id)
    form = DynamicFormForm(obj=d_form)
    form.copy_from.choices = [('0', 'Khong')] + [(f.id, f.name) for f in DynamicForm.query.all()]
    field_form = FormFieldForm()
    delete_form = DeleteForm()

    if form.validate_on_submit():
        d_form.name = form.name.data
        d_form.description = form.description.data
        db.session.commit()
        flash('Bieu mau da duoc cap nhat.', 'success')
        return redirect(url_for('admin.edit_form', form_id=form_id))

    fields = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()
    return render_template(
        'admin/form_edit.html',
        form=form, field_form=field_form,
        d_form=d_form, fields=fields, delete_form=delete_form,
    )


@admin.route('/forms/delete/<int:form_id>', methods=['POST'])
@login_required
@permission_required(Permissions.MANAGE_FORMS)
def delete_form(form_id):
    d_form = DynamicForm.query.get_or_404(form_id)
    db.session.delete(d_form)
    db.session.commit()
    flash('Bieu mau da duoc xoa.', 'success')
    return redirect(url_for('admin.manage_forms_list'))


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _smart_redirect(fallback_endpoint):
    if request.referrer and 'dashboard' in request.referrer:
        return redirect(request.referrer)
    return redirect(url_for(fallback_endpoint))
