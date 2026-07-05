from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms.validators import Optional
from wtforms.fields import DateField
from app.models import DynamicForm, Department

class ReportSearchForm(FlaskForm):
    form_id = SelectField('Tên phiếu', coerce=int, choices=[(0, 'Tất cả')], default=0)
    department_id = SelectField('Khoa/Phòng', coerce=int, choices=[(0, 'Tất cả')], default=0)
    status = SelectField('Trạng thái', choices=[
        ('', 'Tất cả'),
        ('approved', 'Đã duyệt'),
        ('pending', 'Chờ duyệt'),
        ('rejected', 'Từ chối')
    ], default='')
    start_date = DateField('Từ ngày', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('Đến ngày', format='%Y-%m-%d', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(ReportSearchForm, self).__init__(*args, **kwargs)
        self.form_id.choices = [(0, 'Tất cả')] + [(f.id, f.name) for f in DynamicForm.query.all()]
        self.department_id.choices = [(0, 'Tất cả')] + [(d.id, d.name) for d in Department.query.all()]
