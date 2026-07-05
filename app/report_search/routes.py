from flask import render_template, request, send_file
from flask_login import login_required
from . import report_search_bp
from .forms import ReportSearchForm
from app.models import FormSubmission, Patient
from datetime import datetime
import io
import openpyxl

@report_search_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = ReportSearchForm()
    results = []
    searched = False
    
    if request.method == 'POST':
        searched = True
        form_id = form.form_id.data
        department_id = form.department_id.data
        status = form.status.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        
        query = FormSubmission.query.join(FormSubmission.patient)
        
        if form_id and form_id > 0:
            query = query.filter(FormSubmission.form_id == form_id)
        if department_id and department_id > 0:
            query = query.filter(Patient.department_id == department_id)
        if status:
            query = query.filter(FormSubmission.status == status)
        if start_date:
            query = query.filter(FormSubmission.submitted_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(FormSubmission.submitted_at <= datetime.combine(end_date, datetime.max.time()))
            
        results = query.order_by(FormSubmission.submitted_at.desc()).all()
        
        # Check if this is an export request
        export_type = request.form.get('export_action')
        if export_type in ['xlsx', 'xls', 'data']:
            # Generate Excel file
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Báo cáo tra cứu"
            
            # Header
            headers = ['STT', 'Mã BN', 'Họ Tên', 'Ngày Sinh', 'Giới Tính', 'Mã BHYT', 'Tên Phiếu', 'Khoa/Phòng', 'Ngày Nhận', 'Trạng Thái']
            ws.append(headers)
            
            # Data
            for idx, sub in enumerate(results, 1):
                dob = sub.patient.date_of_birth.strftime('%d/%m/%Y') if sub.patient.date_of_birth else ''
                dept = sub.patient.department.name if sub.patient.department else ''
                status_text = 'Đã duyệt' if sub.status == 'approved' else ('Từ chối' if sub.status == 'rejected' else 'Chờ duyệt')
                
                row = [
                    idx,
                    sub.patient.patient_code,
                    sub.patient.full_name,
                    dob,
                    sub.patient.gender,
                    sub.patient.bhyt,
                    sub.form.name,
                    dept,
                    sub.submitted_at.strftime('%d/%m/%Y %H:%M'),
                    status_text
                ]
                ws.append(row)
                
            out = io.BytesIO()
            wb.save(out)
            out.seek(0)
            
            return send_file(
                out,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f"BaoCaoTraCuu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
    
    return render_template('report_search/index.html', form=form, results=results, searched=searched)
