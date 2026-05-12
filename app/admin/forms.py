"""
Forms cho admin blueprint.
Chi giu lai cac form thuc su duoc su dung.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, DateField, SelectField, TextAreaField,
                     SubmitField, PasswordField, BooleanField, IntegerField)
from wtforms.fields import MultipleFileField
from wtforms.validators import DataRequired, Email, Optional, EqualTo, ValidationError

from ..models import User, Department
from ..extensions import db


class ChangePasswordForm(FlaskForm):
    old_password  = PasswordField('Mat khau cu',  validators=[DataRequired()])
    new_password  = PasswordField('Mat khau moi', validators=[DataRequired()])
    new_password2 = PasswordField('Xac nhan mat khau moi',
                                  validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Doi mat khau')


class DepartmentForm(FlaskForm):
    name   = StringField('Ten khoa', validators=[DataRequired()])
    submit = SubmitField('Them khoa')


class EditUserForm(FlaskForm):
    username    = StringField('Ten dang nhap', validators=[DataRequired()])
    full_name   = StringField('Ho va ten',     validators=[DataRequired()])
    email       = StringField('Email',         validators=[Optional(), Email()])
    role        = SelectField('Vai tro',
                              choices=[('staff', 'Nhan vien'),
                                       ('finance', 'Tai chinh'),
                                       ('admin', 'Quan tri vien')],
                              validators=[DataRequired()])
    department  = SelectField('Khoa', coerce=int, validators=[Optional()])
    parent_user = SelectField('Nguoi dung cha', coerce=int, validators=[Optional()])
    locked      = BooleanField('Khoa tai khoan')
    password    = PasswordField('Mat khau moi', validators=[Optional()])
    password2   = PasswordField('Xac nhan mat khau moi',
                                validators=[Optional(), EqualTo('password', 'Mat khau khong khop.')])
    submit = SubmitField('Cap nhat')

    def __init__(self, original_email, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_email    = original_email
        self.original_username = original_username
        self.department.choices  = [(0, 'Khong co')] + [(d.id, d.name) for d in Department.query.order_by('name').all()]
        self.parent_user.choices = [(0, 'Khong co')] + [(u.id, u.username) for u in User.query.order_by('username').all()]

    def validate_email(self, email):
        if email.data and email.data != self.original_email:
            with db.session.no_autoflush:
                if User.query.filter_by(email=email.data).first():
                    raise ValidationError('Email da duoc dang ky.')

    def validate_username(self, username):
        if username.data != self.original_username:
            if User.query.filter_by(username=username.data).first():
                raise ValidationError('Ten dang nhap da ton tai.')


class CreateUserForm(FlaskForm):
    username    = StringField('Ten dang nhap', validators=[Optional()])
    full_name   = StringField('Ho va ten',     validators=[DataRequired()])
    department  = SelectField('Khoa', coerce=int, validators=[Optional()])
    email       = StringField('Email',         validators=[Optional(), Email()])
    password    = PasswordField('Mat khau',    validators=[DataRequired()])
    password2   = PasswordField('Xac nhan mat khau',
                                validators=[DataRequired(), EqualTo('password', 'Mat khau khong khop.')])
    role        = SelectField('Vai tro',
                              choices=[('admin', 'Quan tri vien'),
                                       ('staff', 'Nhan vien'),
                                       ('finance', 'Tai chinh')],
                              validators=[DataRequired()])
    parent_user = SelectField('Nguoi quan ly', coerce=int, choices=[], validators=[Optional()])
    locked      = BooleanField('Khoa tai khoan')
    submit = SubmitField('Tao nguoi dung')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.department.choices  = [(0, 'Khong co')] + [(d.id, d.name) for d in Department.query.order_by('name').all()]
        self.parent_user.choices = [(0, 'Khong co')] + [(u.id, u.username) for u in User.query.order_by('username').all()]

    def validate_email(self, email):
        if email.data and email.data.strip():
            with db.session.no_autoflush:
                if User.query.filter_by(email=email.data.strip()).first():
                    raise ValidationError('Email da duoc dang ky.')

    def validate_username(self, username):
        if username.data:
            with db.session.no_autoflush:
                if User.query.filter_by(username=username.data).first():
                    raise ValidationError('Ten dang nhap da ton tai.')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class DeleteForm(FlaskForm):
    submit = SubmitField('Delete')


class DynamicFormForm(FlaskForm):
    """Form tao/sua bieu mau dong."""
    name           = StringField('Ten Bieu mau',   validators=[DataRequired()])
    description    = TextAreaField('Mo ta')
    requester_name = StringField('Nguoi yeu cau',  validators=[Optional()])
    department     = StringField('Khoa/Phong',     validators=[Optional()])
    copy_from      = SelectField('Sao chep tu Bieu mau da co', coerce=int, validators=[Optional()])
    submit = SubmitField('Luu Bieu mau')


class FormFieldForm(FlaskForm):
    """Form them/sua truong trong bieu mau dong."""
    label      = StringField('Nhan Truong', validators=[DataRequired()])
    field_type = SelectField('Loai Truong', choices=[
        ('text',           'Text'),
        ('textarea',       'Text Area'),
        ('datetime-local', 'Ngay va gio'),
        ('select',         'Select'),
        ('department',     'Khoa/Phong'),
    ], validators=[DataRequired()])
    options             = TextAreaField('Tuy chon (moi tuy chon mot dong)')
    required            = BooleanField('Bat buoc')
    order               = IntegerField('Thu tu', default=0)
    requester_signature = TextAreaField('Nguoi yeu cau')
    it_signature        = TextAreaField('Phong KHTH/CNTT')
    submit = SubmitField('Luu Truong')

    def validate_options(self, field):
        if self.field_type.data == 'select' and not field.data:
            raise ValidationError('Truong tuy chon la bat buoc khi loai truong la Select.')


class ManagePermissionForm(FlaskForm):
    submit = SubmitField('Luu thay doi')
