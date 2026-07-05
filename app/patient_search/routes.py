from flask import render_template, request, redirect, url_for, flash
from . import patient_search_bp
from .forms import PatientSearchForm
from app.models import FormSubmission, DynamicForm, Patient, Department
from app.extensions import db
from datetime import datetime

@patient_search_bp.route('/search', methods=['GET', 'POST'])
def search():
    form = PatientSearchForm()
    form.form_name.choices = [('', 'Tất cả')] + [(f.name, f.name) for f in DynamicForm.query.all()]
    form.department_id.choices = [(0, 'Tất cả')] + [(d.id, d.name) for d in Department.query.all()]
    results = []
    searched = False
    if form.validate_on_submit():
        searched = True
        patient_code = form.patient_code.data
        patient_name = form.patient_name.data
        ma_bhyt = form.ma_bhyt.data
        phone = form.phone.data
        exact_match = form.exact_match.data
        
        form_name = form.form_name.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        status = form.status.data
        department_id = form.department_id.data

        query = FormSubmission.query.join(FormSubmission.patient)

        filters = []
        if patient_code:
            filters.append(Patient.patient_code == patient_code)
        if patient_name:
            if exact_match:
                filters.append(Patient.full_name == patient_name)
            else:
                filters.append(Patient.full_name.ilike(f'%{patient_name}%'))
        if ma_bhyt:
            filters.append(Patient.bhyt.ilike(f'%{ma_bhyt}%'))
        if phone:
            filters.append(Patient.phone.ilike(f'%{phone}%'))
            
        if start_date:
            filters.append(FormSubmission.submitted_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            filters.append(FormSubmission.submitted_at <= datetime.combine(end_date, datetime.max.time()))
        if status:
            filters.append(FormSubmission.status == status)
        if department_id and department_id > 0:
            filters.append(Patient.department_id == department_id)

        if form_name:
            form_template = DynamicForm.query.filter(DynamicForm.name == form_name).first()
            if form_template:
                filters.append(FormSubmission.form_id == form_template.id)
            else:
                flash('Không tìm thấy tên biểu mẫu.', 'warning')

        if filters:
            query = query.filter(*filters)
            results = query.all()
        elif searched:
            flash('Vui lòng nhập ít nhất một tiêu chí tìm kiếm.', 'info')

    return render_template('patient_search/search.html', form=form, results=results, searched=searched)