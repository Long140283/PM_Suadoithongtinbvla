from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import Optional
from wtforms.fields import DateField
from app.models import DynamicForm, Department

class ActivityReportForm(FlaskForm):
    form_id = SelectField('Chọn biểu mẫu', coerce=int)
    department_id = SelectField('Chọn khoa', coerce=int, choices=[(0, 'Tất cả')], default=0)
    start_date = DateField('Từ ngày', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('Đến ngày', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Xem báo cáo')

    def __init__(self, *args, **kwargs):
        super(ActivityReportForm, self).__init__(*args, **kwargs)
        self.form_id.choices = [(f.id, f.name) for f in DynamicForm.query.all()]
        self.department_id.choices = [(0, 'Tất cả')] + [(d.id, d.name) for d in Department.query.all()]