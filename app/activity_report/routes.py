from flask import render_template, request, redirect, url_for, flash, Response
from urllib.parse import quote
from app.activity_report import activity_report_bp
from app.activity_report.forms import ActivityReportForm
from app.models import DynamicForm, FormSubmission, FormField, User, Attachment
from app.extensions import db
import pandas as pd
from io import BytesIO
from datetime import datetime

from flask_login import login_required, current_user

@activity_report_bp.route('/', methods=['GET', 'POST'])
@login_required
def activity_report():
    form = ActivityReportForm()
    submissions = []
    form_fields = []
    form_name = ''

    if form.validate_on_submit() or request.args.get('export') == 'excel':
        form_id = form.form_id.data if form.validate_on_submit() else request.args.get('form_id')
        department_id = form.department_id.data if form.validate_on_submit() else request.args.get('department_id', type=int)
        start_date = form.start_date.data if form.validate_on_submit() else (datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date() if request.args.get('start_date') else None)
        end_date = form.end_date.data if form.validate_on_submit() else (datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date() if request.args.get('end_date') else None)

        query = FormSubmission.query.filter_by(form_id=form_id)

        if department_id and department_id > 0:
            query = query.join(User, FormSubmission.user_id == User.id).filter(User.department_id == department_id)

        if start_date:
            query = query.filter(FormSubmission.submitted_at >= start_date)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(FormSubmission.submitted_at <= end_datetime)

        submissions = query.all()
        for sub in submissions:
            sub.attachments = Attachment.query.filter_by(form_submission_id=sub.id).all()
        dynamic_form = DynamicForm.query.get(form_id)
        form_name = dynamic_form.name
        form_fields = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()

        if request.args.get('export') == 'excel':
            data = []
            for submission in submissions:
                submission_data = {
                    'Submission ID': submission.id,
                    'Submitted At': submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'Submitted By': submission.user.username,
                    'Department': submission.user.department.name if submission.user.department else 'N/A',
                    'Status': submission.status
                }
                for field in form_fields:
                    value = next((v.value for v in submission.values if v.field_id == field.id), '')
                    submission_data[field.label] = value
                
                attachments = Attachment.query.filter_by(form_submission_id=submission.id).all()
                attachment_info = []
                for att in attachments:
                    # Construct full URL for the attachment
                    url = url_for('patient.serve_attachment', attachment_id=att.id, _external=True)
                    attachment_info.append(f"{att.filename}: {url}")
                
                submission_data['Attachments'] = "\n".join(attachment_info)

                data.append(submission_data)

            df = pd.DataFrame(data)

            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Activity Report', index=False)
            
            # Access the xlsxwriter workbook and worksheet objects
            workbook  = writer.book
            worksheet = writer.sheets['Activity Report']
            
            # Add formats
            link_format = workbook.add_format({'font_color': 'blue', 'underline': 1})
            wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
            
            # Find the "Attachments" column index
            try:
                col_idx = df.columns.get_loc('Attachments')
                # Set column width and wrap text
                worksheet.set_column(col_idx, col_idx, 50, wrap_format)
                
                # Iterate through the rows and write URLs
                for row_num, attachment_text in enumerate(df['Attachments']):
                    if attachment_text:
                        lines = attachment_text.split('\n')
                        if len(lines) == 1 and ': http' in lines[0]:
                            parts = lines[0].split(': ', 1)
                            if len(parts) == 2:
                                label, url = parts
                                worksheet.write_url(row_num + 1, col_idx, url, string=label, cell_format=link_format)
                        else:
                            # For multiple attachments, just ensure they are wrapped
                            worksheet.write(row_num + 1, col_idx, attachment_text, wrap_format)
            except Exception as e:
                logger.error(f"Error adding hyperlinks to Excel: {e}")

            writer.close()
            output.seek(0)

            filename = f"activity_report_{form_name}.xlsx"
            return Response(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": "attachment; filename*=UTF-8''{}".format(quote(filename))})

    return render_template('activity_report/activity_report.html', form=form, submissions=submissions, form_fields=form_fields, form_name=form_name)