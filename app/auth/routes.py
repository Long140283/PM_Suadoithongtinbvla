from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from .forms import LoginForm, AdminRegistrationForm
from ..models import User, Role
from ..extensions import db

from sqlalchemy import func, collate

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def user_has_role(user, role_name):
    """Kiểm tra xem người dùng có vai trò cụ thể không."""
    return role_name in [role.name for role in user.roles]

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        user_roles = [role.name for role in current_user.roles]
        if 'admin' in user_roles:
            return redirect(url_for('admin.dashboard'))
        elif 'finance' in user_roles:
            return redirect(url_for('patient.finance_dashboard'))
        elif 'staff' in user_roles:
            return redirect(url_for('patient.staff_dashboard'))
        else:
            flash('Vai trò người dùng không xác định, vui lòng liên hệ quản trị viên.')
            return redirect(url_for('auth.logout'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (func.lower(User.email) == func.lower(form.email.data).collate("NOCASE")) | (func.lower(User.username) == func.lower(form.email.data).collate("NOCASE"))
        ).first()
        if user:
            if user.password_hash is None:
                flash('Tài khoản của bạn không có mật khẩu. Vui lòng liên hệ quản trị viên để đặt lại.')
                return redirect(url_for('auth.login'))
            
            if user.check_password(form.password.data):
                if user.locked:
                    flash('Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên.')
                    return redirect(url_for('auth.login'))
                
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                
                user_roles = [role.name for role in user.roles]

                if next_page:
                    if ('admin' in next_page or 'finance' in next_page) and 'admin' not in user_roles and 'finance' not in user_roles:
                        pass # Ignore next_page to prevent 403 Forbidden
                    else:
                        return redirect(next_page)
                if 'admin' in user_roles:
                    return redirect(url_for('admin.dashboard'))
                elif 'finance' in user_roles:
                    return redirect(url_for('patient.finance_dashboard'))
                elif 'staff' in user_roles:
                    return redirect(url_for('patient.staff_dashboard'))
                else:
                    flash('Vai trò người dùng không xác định, vui lòng liên hệ quản trị viên.')
                    return redirect(url_for('auth.logout'))
        
        flash('Tên đăng nhập/email hoặc mật khẩu không hợp lệ')
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register_admin', methods=['GET', 'POST'])
@login_required
def register_admin():
    if not user_has_role(current_user, 'admin'):
        flash('Only admins can register new admins.')
        return redirect(url_for('admin.dashboard'))
    form = AdminRegistrationForm()
    if form.validate_on_submit():
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            flash('Admin role not found. Please create it first.')
            return redirect(url_for('admin.dashboard'))
            
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.roles.append(admin_role)
        db.session.add(user)
        db.session.commit()
        flash('New admin registered successfully.')
        return redirect(url_for('admin.dashboard'))
    return render_template('register_admin.html', form=form)