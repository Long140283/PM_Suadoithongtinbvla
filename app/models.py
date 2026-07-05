"""
Models SQLAlchemy cho toan bo ung dung.
Chi giu lai cac model thuc su duoc su dung.
"""
from .extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

# ---------------------------------------------------------------------------
# Bang lien ket nhieu-nhieu
# ---------------------------------------------------------------------------

user_permissions = db.Table(
    'user_permissions',
    db.Column('user_id',       db.Integer, db.ForeignKey('user.id'),       primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True),
)

role_permissions = db.Table(
    'role_permissions',
    db.Column('role_id',       db.Integer, db.ForeignKey('role.id'),       primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True),
)

user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
)


# ---------------------------------------------------------------------------
# Phan quyen
# ---------------------------------------------------------------------------

class Permission(db.Model):
    __tablename__ = 'permission'
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(50),  unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=True)
    hidden       = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Permission {self.name}>'


class Role(db.Model):
    __tablename__ = 'role'
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    permissions = db.relationship(
        'Permission', secondary=role_permissions, lazy='dynamic',
        backref=db.backref('roles', lazy=True),
    )

    def __repr__(self):
        return f'<Role {self.name}>'


# ---------------------------------------------------------------------------
# Nguoi dung
# ---------------------------------------------------------------------------

class Department(db.Model):
    __tablename__ = 'department'
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    users = db.relationship('User', backref='department', lazy=True)

    def __repr__(self):
        return f'<Department {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64),  unique=True, nullable=True,  index=True)
    full_name     = db.Column(db.String(128), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    email         = db.Column(db.String(120), unique=True, nullable=True,  index=True)
    password_hash = db.Column(db.String(256), nullable=True)
    locked        = db.Column(db.Boolean, nullable=False, default=False)
    parent_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    last_notification_read = db.Column(db.DateTime, nullable=True)

    roles = db.relationship(
        'Role', secondary=user_roles, lazy='dynamic',
        backref=db.backref('users', lazy=True),
    )
    permissions = db.relationship(
        'Permission', secondary=user_permissions, lazy='dynamic',
        backref=db.backref('users', lazy=True),
    )
    parent = db.relationship('User', remote_side=[id], backref=db.backref('children', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission_name, ignore_hidden=False):
        perm = Permission.query.filter_by(name=permission_name).first()
        if not ignore_hidden and perm and perm.hidden:
            return False
            
        if self.is_admin():
            return True
        if any(p.name == permission_name for p in self.permissions):
            return True
        for role in self.roles:
            if any(p.name == permission_name for p in role.permissions):
                return True
        return False

    def get_permission_names(self):
        user_perms = {p.name for p in self.permissions}
        role_perms = {p.name for role in self.roles for p in role.permissions}
        return user_perms | role_perms

    def is_admin(self):
        return any(role.name == 'admin' for role in self.roles)

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

    @property
    def role(self):
        first = self.roles.first()
        return first.name if first else None

    @property
    def is_finance(self):
        return self.has_role('finance')

    def __repr__(self):
        return f'<User {self.username}>'


# ---------------------------------------------------------------------------
# Benh nhan
# ---------------------------------------------------------------------------

class Patient(db.Model):
    __tablename__ = 'patient'
    id              = db.Column(db.Integer, primary_key=True)
    department_id   = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    patient_code    = db.Column(db.String(64),  nullable=True, index=True)
    full_name       = db.Column(db.String(128), nullable=False)
    date_of_birth   = db.Column(db.Date,        nullable=True)
    gender          = db.Column(db.String(10),  nullable=True)
    address         = db.Column(db.String(256), nullable=True)
    bhyt            = db.Column(db.String(64),  nullable=True)
    phone           = db.Column(db.String(20),  nullable=True)
    email           = db.Column(db.String(120), nullable=True)
    medical_history = db.Column(db.Text,        nullable=True)
    status          = db.Column(db.String(20),  nullable=False, default='pending')
    timestamp       = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)
    user_id         = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    department = db.relationship('Department', backref=db.backref('patients', lazy=True))
    user       = db.relationship('User',       backref=db.backref('patients', lazy=True))

    def __repr__(self):
        return f'<Patient {self.patient_code} - {self.full_name}>'


# ---------------------------------------------------------------------------
# Bieu mau dong
# ---------------------------------------------------------------------------

class DynamicForm(db.Model):
    __tablename__ = 'dynamic_form'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status      = db.Column(db.String(50), default='active', nullable=False)


    fields      = db.relationship('FormField',      backref='form', lazy='dynamic',
                                  cascade='all, delete-orphan')
    submissions = db.relationship('FormSubmission', backref='form', lazy='dynamic',
                                  cascade='all, delete-orphan')
    user        = db.relationship('User', backref=db.backref('dynamic_forms', lazy=True))

    def __repr__(self):
        return f'<DynamicForm {self.name}>'


class FormField(db.Model):
    __tablename__ = 'form_field'
    id                  = db.Column(db.Integer, primary_key=True)
    form_id             = db.Column(db.Integer, db.ForeignKey('dynamic_form.id'), nullable=False)
    label               = db.Column(db.String(100), nullable=False)
    field_type          = db.Column(db.String(50),  nullable=False)
    options             = db.Column(db.Text, nullable=True)
    required            = db.Column(db.Boolean, default=False, nullable=False)
    order               = db.Column(db.Integer, nullable=False, default=0)
    requester_signature = db.Column(db.Text, nullable=True)
    it_signature        = db.Column(db.Text, nullable=True)

    def set_options(self, options_list):
        self.options = json.dumps(options_list, ensure_ascii=False)

    def get_options(self):
        if self.options:
            try:
                return json.loads(self.options)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    @property
    def options_list(self):
        return self.get_options()

    def __repr__(self):
        return f'<FormField {self.label}>'


class FormSubmission(db.Model):
    __tablename__ = 'form_submission'
    id               = db.Column(db.Integer, primary_key=True)
    form_id          = db.Column(db.Integer, db.ForeignKey('dynamic_form.id'), nullable=False)
    user_id          = db.Column(db.Integer, db.ForeignKey('user.id'),         nullable=False)
    patient_id       = db.Column(db.Integer, db.ForeignKey('patient.id'),      nullable=True)
    submitted_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status           = db.Column(db.String(50), default='pending_finance', nullable=False, index=True)
    direct_to_admin  = db.Column(db.Boolean, default=False)
    rejection_reason = db.Column(db.Text, nullable=True)
    approved_by_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    values      = db.relationship('SubmissionValue', backref='submission', lazy='dynamic',
                                  cascade='all, delete-orphan')
    user        = db.relationship('User', backref='form_submissions', foreign_keys=[user_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    patient     = db.relationship('Patient', backref='form_submissions')

    @property
    def request_date(self):
        return self.submitted_at

    def __repr__(self):
        return f'<FormSubmission id={self.id} status={self.status}>'


class SubmissionValue(db.Model):
    __tablename__ = 'submission_value'
    id            = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('form_submission.id'), nullable=False)
    field_id      = db.Column(db.Integer, db.ForeignKey('form_field.id'),      nullable=False)
    value         = db.Column(db.Text, nullable=False)
    field         = db.relationship('FormField')

    def __repr__(self):
        return f'<SubmissionValue field={self.field_id}>'


# ---------------------------------------------------------------------------
# Tep dinh kem
# ---------------------------------------------------------------------------

class Attachment(db.Model):
    __tablename__ = 'attachment'
    id                 = db.Column(db.Integer, primary_key=True)
    patient_id         = db.Column(db.Integer, db.ForeignKey('patient.id'),      nullable=True)
    form_submission_id = db.Column(db.Integer, db.ForeignKey('form_submission.id'), nullable=True)
    request_type       = db.Column(db.String(50),  nullable=True)
    filename           = db.Column(db.String(128), nullable=False)
    file_path          = db.Column(db.String(256), nullable=False)
    mimetype           = db.Column(db.String(50),  nullable=False)
    uploaded_at        = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    patient    = db.relationship('Patient',        backref=db.backref('attachments', lazy=True))
    submission = db.relationship('FormSubmission', backref=db.backref('attachments', lazy=True))

    def __repr__(self):
        return f'<Attachment {self.filename}>'


# ---------------------------------------------------------------------------
# Nhat ky kiem toan
# ---------------------------------------------------------------------------

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action    = db.Column(db.String(128), nullable=False)
    details   = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))

    def __repr__(self):
        return f'<AuditLog {self.action} by user_id={self.user_id}>'
