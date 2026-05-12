from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, SelectField
from wtforms.validators import Optional
from app.models import Department, DynamicForm

class PatientSearchForm(FlaskForm):
    patient_code = StringField('Mã bệnh nhân', validators=[Optional()])
    patient_name = StringField('Tên bệnh nhân', validators=[Optional()])
    form_name = SelectField('Tên phiếu', choices=[], validators=[Optional()])
    start_date = DateField('Từ ngày', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('Đến ngày', format='%Y-%m-%d', validators=[Optional()])
    status = SelectField('Trạng thái', choices=[
        ('', 'Tất cả'),
        ('approved', 'Đã duyệt'),
        ('pending', 'Chờ duyệt'),
        ('rejected', 'Từ chối')
    ], validators=[Optional()])
    department_id = SelectField('Khoa', coerce=int, validators=[Optional()])
    submit = SubmitField('Tìm kiếm')