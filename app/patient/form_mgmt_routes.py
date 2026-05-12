"""Routes quan ly bieu mau dong danh cho staff/admin."""
import logging
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import DynamicForm, FormField
from app.admin.forms import DynamicFormForm, FormFieldForm, DeleteForm
from app.patient import patient_bp

logger = logging.getLogger(__name__)


def _check_form_owner(d_form):
    return d_form.user_id == current_user.id or current_user.is_admin()


@patient_bp.route('/forms')
@login_required
def list_user_forms():
    forms = DynamicForm.query.filter_by(user_id=current_user.id).all()
    return render_template('admin/forms.html', forms=forms)


@patient_bp.route('/forms/create', methods=['GET', 'POST'])
@login_required
def create_form():
    form = DynamicFormForm()
    if request.method == 'GET':
        form.requester_name.data = f'{current_user.username} - {current_user.full_name}'
        if current_user.department:
            form.department.data = current_user.department.name
    if form.validate_on_submit():
        new_form = DynamicForm(name=form.name.data, description=form.description.data, user_id=current_user.id)
        db.session.add(new_form)
        db.session.commit()
        flash('Bieu mau da duoc tao.', 'success')
        return redirect(url_for('patient.edit_form', form_id=new_form.id))
    return render_template('admin/form_create.html', form=form)



@patient_bp.route('/forms/edit/<int:form_id>', methods=['GET', 'POST'])
@login_required
def edit_form(form_id):
    d_form = DynamicForm.query.get_or_404(form_id)
    if not _check_form_owner(d_form):
        flash('Ban khong co quyen chinh sua bieu mau nay.', 'danger')
        return redirect(url_for('patient.staff_dashboard'))
    form = DynamicFormForm(obj=d_form)
    field_form = FormFieldForm()
    delete_form = DeleteForm()
    if form.validate_on_submit():
        d_form.name = form.name.data
        d_form.description = form.description.data
        db.session.commit()
        flash('Bieu mau da duoc cap nhat.', 'success')
        return redirect(url_for('patient.list_user_forms'))
    return render_template('admin/form_edit.html', form=form, d_form=d_form, field_form=field_form, delete_form=delete_form)


@patient_bp.route('/forms/delete/<int:form_id>', methods=['POST'])
@login_required
def delete_form(form_id):
    d_form = DynamicForm.query.get_or_404(form_id)
    if not _check_form_owner(d_form):
        flash('Ban khong co quyen xoa bieu mau nay.', 'danger')
        return redirect(url_for('patient.staff_dashboard'))
    db.session.delete(d_form)
    db.session.commit()
    flash('Bieu mau da duoc xoa.', 'success')
    return redirect(url_for('patient.list_user_forms'))


@patient_bp.route('/forms/<int:form_id>/add_field', methods=['POST'])
@login_required
def add_field(form_id):
    d_form = DynamicForm.query.get_or_404(form_id)
    if not _check_form_owner(d_form):
        flash('Ban khong co quyen chinh sua bieu mau nay.', 'danger')
        return redirect(url_for('patient.staff_dashboard'))
    form = FormFieldForm()
    if form.validate_on_submit():
        options = ([opt.strip() for opt in form.options.data.splitlines()] if form.field_type.data == 'select' else [])
        new_field = FormField(
            form_id=d_form.id, label=form.label.data, field_type=form.field_type.data,
            required=form.required.data, order=form.order.data,
            requester_signature=form.requester_signature.data, it_signature=form.it_signature.data,
        )
        new_field.set_options(options)
        db.session.add(new_field)
        db.session.commit()
        flash('Truong da duoc them.', 'success')
    else:
        flash('Loi khi them truong.', 'danger')
    return redirect(url_for('patient.edit_form', form_id=form_id))


@patient_bp.route('/forms/field/edit/<int:field_id>', methods=['GET', 'POST'])
@login_required
def edit_field(field_id):
    field = FormField.query.get_or_404(field_id)
    if not _check_form_owner(field.form):
        flash('Ban khong co quyen chinh sua bieu mau nay.', 'danger')
        return redirect(url_for('patient.staff_dashboard'))
    form = FormFieldForm(obj=field)
    if form.validate_on_submit():
        field.label = form.label.data
        field.field_type = form.field_type.data
        field.required = form.required.data
        field.order = form.order.data
        options = ([opt.strip() for opt in form.options.data.splitlines()] if form.field_type.data == 'select' else [])
        field.set_options(options)
        db.session.commit()
        flash('Truong da duoc cap nhat.', 'success')
        return redirect(url_for('patient.edit_form', form_id=field.form_id))
    return render_template('admin/field_edit.html', form=form, field=field)


@patient_bp.route('/forms/field/delete/<int:field_id>', methods=['POST'])
@login_required
def delete_field(field_id):
    field = FormField.query.get_or_404(field_id)
    if not _check_form_owner(field.form):
        flash('Ban khong co quyen chinh sua bieu mau nay.', 'danger')
        return redirect(url_for('patient.staff_dashboard'))
    form_id = field.form_id
    db.session.delete(field)
    db.session.commit()
    flash('Truong da duoc xoa.', 'success')
    return redirect(url_for('patient.edit_form', form_id=form_id))


@patient_bp.route('/forms/field/move_up/<int:field_id>', methods=['POST'])
@login_required
def move_field_up(field_id):
    return _move_field(field_id, 'up')


@patient_bp.route('/forms/field/move_down/<int:field_id>', methods=['POST'])
@login_required
def move_field_down(field_id):
    return _move_field(field_id, 'down')


def _move_field(field_id, direction):
    field = FormField.query.get_or_404(field_id)
    if not _check_form_owner(field.form):
        flash('Ban khong co quyen chinh sua bieu mau nay.', 'danger')
        return redirect(url_for('patient.staff_dashboard'))
    all_fields = FormField.query.filter_by(form_id=field.form_id).order_by(FormField.order, FormField.id).all()
    for i, f in enumerate(all_fields):
        f.order = i + 1
    db.session.flush()
    field = FormField.query.get(field_id)
    target = field.order - 1 if direction == 'up' else field.order + 1
    neighbor = FormField.query.filter_by(form_id=field.form_id, order=target).first()
    if neighbor:
        field.order, neighbor.order = neighbor.order, field.order
    db.session.commit()
    return redirect(url_for('patient.edit_form', form_id=field.form_id))
