"""
Routes xu ly phieu (FormSubmission): dien, xem, sua, xoa, in.
"""
import logging
import os
from datetime import datetime

from flask import (render_template, redirect, url_for, flash,
                   request, current_app, send_from_directory)
from flask_login import login_required, current_user
from wtforms import StringField, DateField, SelectField
from wtforms.validators import DataRequired, Optional

from app.extensions import db
from app.models import (DynamicForm, FormField, FormSubmission,
                        SubmissionValue, Attachment, Patient, AuditLog, Permission)
from app.constants import SubmissionStatus, Permissions
from app.utils import save_upload, extract_patient_info
from app.patient.forms import DynamicPatientForm, RejectionForm, generate_dynamic_form

from . import patient_bp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dien phieu
# ---------------------------------------------------------------------------

@patient_bp.route('/dynamic_form/<int:form_id>', methods=['GET', 'POST'])
@login_required
def fill_dynamic_form(form_id):
    d_form = DynamicForm.query.get_or_404(form_id)
    # UI check respects 'hidden', logic check ignores it
    can_show_bypass = current_user.has_permission(Permissions.BYPASS_FINANCE)
    can_bypass_logic = current_user.has_permission(Permissions.BYPASS_FINANCE, ignore_hidden=True)

    # Xay dung form dong
    FormClass = _build_form_class(d_form)
    form = FormClass()

    if request.method == 'GET':
        form.direct_to_admin.data = can_bypass_logic

    if form.validate_on_submit():
        # If hidden from UI, we auto-bypass if user has permission
        is_direct = can_bypass_logic and (form.direct_to_admin.data or not can_show_bypass)
        
        status = (SubmissionStatus.PENDING_ADMIN
                  if is_direct
                  else SubmissionStatus.PENDING_FINANCE)

        sub = FormSubmission(
            form_id=d_form.id,
            user_id=current_user.id,
            direct_to_admin=is_direct,
            status=status,
        )
        db.session.add(sub)
        db.session.flush()  # lay sub.id truoc khi commit

        # Luu gia tri truong
        patient_code = patient_name = None
        for field in d_form.fields.order_by(FormField.order):
            value = request.form.get(field.label, '')
            db.session.add(SubmissionValue(
                submission_id=sub.id,
                field_id=field.id,
                value=value,
            ))
            label_lower = field.label.lower()
            if not patient_code and any(k in label_lower for k in ['ma benh nhan', 'ma bn', 'patient_code']):
                patient_code = value
            if not patient_name and any(k in label_lower for k in ['ho va ten', 'ten benh nhan', 'patient_name']):
                patient_name = value

        # Luu file dinh kem
        for file in request.files.getlist('attachments'):
            path = save_upload(file, 'dynamic_forms')
            if path:
                db.session.add(Attachment(
                    patient_id=current_user.id,
                    form_submission_id=sub.id,
                    request_type='dynamic_form',
                    filename=os.path.basename(path),
                    file_path=path,
                    mimetype=file.mimetype,
                ))

        # Lien ket benh nhan
        if patient_code:
            patient = Patient.query.filter_by(patient_code=patient_code).first()
            if not patient:
                patient = Patient(
                    patient_code=patient_code,
                    full_name=patient_name or 'N/A',
                    user_id=current_user.id,
                )
                db.session.add(patient)
                db.session.flush()
            sub.patient_id = patient.id

        db.session.commit()
        flash('Phieu da duoc gui thanh cong!', 'success')
        return redirect(url_for('patient.staff_dashboard'))

    return render_template(
        'patient/dynamic_form.html',
        form=d_form,
        patient_form=form,
        can_bypass_finance=can_show_bypass,
    )


# ---------------------------------------------------------------------------
# Xem chi tiet
# ---------------------------------------------------------------------------

@patient_bp.route('/dynamic_form_submission/<int:submission_id>')
@login_required
def show_dynamic_form_submission(submission_id):
    sub = FormSubmission.query.get_or_404(submission_id)
    if not _can_view_submission(sub):
        flash('Ban khong co quyen xem yeu cau nay.', 'danger')
        return redirect(url_for('patient.staff_dashboard'))

    attachments = _get_attachments_with_url(sub.id)
    rejection_form = RejectionForm()
    base_template = 'base_minimal.html' if request.args.get('embed') == '1' else 'base.html'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template(
            'patient/_dynamic_form_submission_content.html',
            submission=sub, attachments=attachments, rejection_form=rejection_form,
        )
    return render_template(
        'patient/dynamic_form_submission_detail.html',
        submission=sub, attachments=attachments,
        rejection_form=rejection_form, base_template=base_template,
    )


# ---------------------------------------------------------------------------
# In phieu
# ---------------------------------------------------------------------------

@patient_bp.route('/dynamic_form_submission/print/<int:submission_id>')
@login_required
def print_dynamic_form_submission(submission_id):
    sub = FormSubmission.query.get_or_404(submission_id)
    if not _can_view_submission(sub):
        flash('Ban khong co quyen in yeu cau nay.', 'danger')
        return redirect(url_for('patient.staff_dashboard'))
    return render_template('patient/print_dynamic_form_submission.html', submission=sub)


# ---------------------------------------------------------------------------
# Sua phieu
# ---------------------------------------------------------------------------

@patient_bp.route('/dynamic_form/edit/<int:submission_id>', methods=['GET', 'POST'])
@login_required
def dynamic_form_edit(submission_id):
    sub = FormSubmission.query.get_or_404(submission_id)
    if current_user.id != sub.user_id:
        flash('Ban khong co quyen chinh sua phieu nay.', 'danger')
        return redirect(url_for('patient.staff_dashboard'))

    # UI check respects 'hidden', logic check ignores it
    can_show_bypass = current_user.has_permission(Permissions.BYPASS_FINANCE)
    can_bypass_logic = current_user.has_permission(Permissions.BYPASS_FINANCE, ignore_hidden=True)
    form_structure = _build_form_structure(sub.form)
    FormClass = generate_dynamic_form(form_structure)

    if request.method == 'POST':
        form = FormClass(request.form)
        if form.validate_on_submit():
            # Cap nhat gia tri
            for field in sub.form.fields:
                field_name = f'field_{field.id}'
                if field_name in form:
                    raw = form[field_name].data
                    val_str = raw.strftime('%Y-%m-%d') if hasattr(raw, 'strftime') else (raw or '')
                    
                    # Tim sv ton tai
                    sv = next((v for v in sub.values if v.field_id == field.id), None)
                    if sv:
                        sv.value = val_str
                    else:
                        db.session.add(SubmissionValue(
                            submission_id=sub.id,
                            field_id=field.id,
                            value=val_str
                        ))

            # Luu file moi
            for file in request.files.getlist('attachments'):
                path = save_upload(file, 'dynamic_forms')
                if path:
                    db.session.add(Attachment(
                        patient_id=current_user.id,
                        form_submission_id=sub.id,
                        request_type='dynamic_form',
                        filename=os.path.basename(path),
                        file_path=path,
                        mimetype=file.mimetype,
                    ))

            # If hidden from UI, we auto-bypass if user has permission
            is_direct = can_bypass_logic and (form.direct_to_admin.data or not can_show_bypass)
            sub.status = SubmissionStatus.PENDING_ADMIN if is_direct else SubmissionStatus.PENDING_FINANCE
            sub.direct_to_admin = is_direct
            db.session.commit()
            flash('Phieu da duoc cap nhat!', 'success')
            return redirect(url_for('patient.staff_dashboard'))
        else:
            for errors in form.errors.values():
                for e in errors:
                    flash(e, 'danger')
    else:
        form = FormClass()
        # Pre-fill gia tri hien tai
        for fd in form_structure:
            fname = fd['name']
            field_id = int(fname.split('_')[1])
            for sv in sub.values:
                if sv.field_id == field_id:
                    if fd['field_type'] == 'date':
                        try:
                            form[fname].data = datetime.strptime(sv.value, '%Y-%m-%d').date()
                        except (ValueError, AttributeError, TypeError):
                            pass
                    else:
                        form[fname].data = sv.value
                    break
        form.direct_to_admin.data = can_bypass_logic or sub.direct_to_admin

    return render_template(
        'patient/dynamic_form_edit.html',
        form=form, submission=sub,
        form_structure=form_structure,
        can_bypass_finance=can_show_bypass,
    )


# ---------------------------------------------------------------------------
# Xoa phieu
# ---------------------------------------------------------------------------

@patient_bp.route('/dynamic_form/delete/<int:submission_id>', methods=['POST'])
@login_required
def dynamic_form_delete(submission_id):
    sub = FormSubmission.query.get_or_404(submission_id)
    if current_user.id != sub.user_id and not current_user.is_admin():
        flash('Ban khong co quyen xoa phieu nay.', 'danger')
        return redirect(url_for('patient.staff_dashboard'))
    db.session.delete(sub)
    db.session.commit()
    flash('Phieu da duoc xoa.', 'success')
    return redirect(url_for('patient.staff_dashboard'))


# ---------------------------------------------------------------------------
# Phuc vu file dinh kem
# ---------------------------------------------------------------------------

@patient_bp.route('/uploads/<int:attachment_id>')
@login_required
def serve_attachment(attachment_id):
    att = Attachment.query.get_or_404(attachment_id)
    # Kiem tra quyen: chu so huu hoac admin/finance
    is_owner = (att.submission and att.submission.user_id == current_user.id)
    if not (current_user.is_admin() or is_owner or current_user.is_finance):
        flash('Ban khong co quyen truy cap tep nay.', 'danger')
        return redirect(url_for('patient.staff_dashboard'))
    directory = os.path.dirname(att.file_path)
    filename  = os.path.basename(att.file_path)
    return send_from_directory(directory, filename)


# ---------------------------------------------------------------------------
# Helpers noi bo
# ---------------------------------------------------------------------------

def _can_view_submission(sub):
    return (current_user.id == sub.user_id
            or any(r.name in ['admin', 'finance'] for r in current_user.roles))


def _build_form_class(d_form):
    """Xay dung class form dong tu DynamicForm model."""
    for field in d_form.fields.order_by(FormField.order):
        validators = [DataRequired()] if field.required else [Optional()]
        if field.field_type == 'date':
            setattr(DynamicPatientForm, field.label, DateField(field.label, validators=validators))
        elif field.field_type == 'select':
            choices = [(o, o) for o in field.get_options()]
            setattr(DynamicPatientForm, field.label,
                    SelectField(field.label, choices=choices, validators=validators))
        else:
            setattr(DynamicPatientForm, field.label, StringField(field.label, validators=validators))
    return DynamicPatientForm


def _build_form_structure(d_form):
    return [{
        'name':       f'field_{f.id}',
        'label':      f.label,
        'field_type': f.field_type,
        'options':    f.get_options(),
        'required':   f.required,
    } for f in d_form.fields.order_by(FormField.order)]


def _get_attachments_with_url(submission_id):
    atts = Attachment.query.filter_by(form_submission_id=submission_id).all()
    static_folder = os.path.join(current_app.root_path, 'static')
    for att in atts:
        try:
            rel = os.path.relpath(att.file_path, static_folder)
            att.url_path = rel.replace('\\', '/')
        except ValueError:
            att.url_path = None
    return atts
