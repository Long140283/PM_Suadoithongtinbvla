"""
Forms cho patient blueprint.
"""
from flask_wtf import FlaskForm
from wtforms import (StringField, DateField, SelectField, TextAreaField,
                     SubmitField, BooleanField, PasswordField)
from wtforms.fields import MultipleFileField
from wtforms.validators import DataRequired, Email, Optional, Length, EqualTo


class DirectToAdminMixin:
    """Mixin them checkbox 'gui thang cho admin'."""
    direct_to_admin = BooleanField('Gui thang cho admin (bo qua duyet tai chinh)')


def generate_dynamic_form(form_structure):
    """
    Tao class form dong tu danh sach mo ta truong.
    form_structure: list of dict {name, label, field_type, options, required}
    """
    class DynamicForm(FlaskForm, DirectToAdminMixin):
        attachments = MultipleFileField('Tep dinh kem')
        submit      = SubmitField('Nop')

    for fd in form_structure:
        fname      = fd['name']
        flabel     = fd['label']
        ftype      = fd['field_type']
        validators = [DataRequired()] if fd.get('required') else [Optional()]

        if ftype == 'date':
            field = DateField(flabel, validators=validators)
        elif ftype == 'select':
            choices = [(o, o) for o in fd.get('options', [])]
            field = SelectField(flabel, choices=choices, validators=validators)
        else:
            field = StringField(flabel, validators=validators)

        setattr(DynamicForm, fname, field)

    return DynamicForm


class DynamicPatientForm(FlaskForm, DirectToAdminMixin):
    """Form dong co the gan them truong bang setattr."""
    attachments = MultipleFileField('Tep dinh kem')
    submit      = SubmitField('Nop')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class RejectionForm(FlaskForm):
    reason = TextAreaField('Ly do tu choi', validators=[DataRequired()])
    submit = SubmitField('Tu choi')


class ChangePasswordForm(FlaskForm):
    old_password     = PasswordField('Mat khau cu',  validators=[DataRequired()])
    new_password     = PasswordField('Mat khau moi', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Xac nhan mat khau moi',
                                     validators=[DataRequired(),
                                                 EqualTo('new_password', message='Mat khau xac nhan khong khop')])
    submit = SubmitField('Doi mat khau')
