import logging
import random
import string

from flask import render_template, redirect, url_for, flash, request, abort, send_file
from sqlalchemy import func
from flask_login import login_required, current_user

from app.admin.forms import EditUserForm, CreateUserForm, DepartmentForm, ChangePasswordForm
from app.extensions import db
from app.models import User, Department, Role, AuditLog, Patient, FormSubmission, DynamicForm
from app.decorators import permission_required
from app.constants import Permissions, Roles
from . import admin

logger = logging.getLogger(__name__)


@admin.route('/users')
@login_required
@permission_required(Permissions.MANAGE_USERS)
def users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@admin.route('/user/new', methods=['GET', 'POST'])
@login_required
@permission_required(Permissions.MANAGE_USERS)
def new_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        role_obj = Role.query.filter_by(name=form.role.data).first()
        if not role_obj:
            flash('Vai trò không tồn tại.', 'danger')
            return render_template('admin_user_form.html', form=form, title='Tạo người dùng mới')
        email_data = form.email.data if form.email.data else None
        user = User(
            username=form.username.data,
            full_name=form.full_name.data,
            email=email_data,
            department_id=form.department.data if form.department.data else None,
            parent_id=form.parent_user.data if form.parent_user.data else None,
            locked=form.locked.data
        )
        user.roles.append(role_obj)
        if form.password.data:
            user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Người dùng đã được tạo.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin_user_form.html', form=form, title='Tạo người dùng mới')


@admin.route('/user/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required(Permissions.MANAGE_USERS)
def edit_user(id):
    user = User.query.get_or_404(id)
    form = EditUserForm(original_email=user.email, original_username=user.username, obj=user)
    if form.validate_on_submit():
        new_email = form.email.data
        if new_email != user.email:
            if not new_email:
                user.email = None
            else:
                existing_user = User.query.filter(User.email == new_email).first()
                if existing_user:
                    flash('Địa chỉ email đã tồn tại.', 'danger')
                    return render_template('admin_user_form.html', form=form, user=user, title='Chỉnh sửa người dùng')
                user.email = new_email

        user.username = form.username.data
        user.full_name = form.full_name.data
        
        # Update role
        role_obj = Role.query.filter_by(name=form.role.data).first()
        if role_obj:
            for r in user.roles.all():
                user.roles.remove(r)
            user.roles.append(role_obj)
        else:
            flash('Vai trò không tồn tại.', 'danger')
            return render_template('admin_user_form.html', form=form, user=user, title='Chỉnh sửa người dùng')
        user.department_id = form.department.data if form.department.data else None
        user.parent_id = form.parent_user.data if form.parent_user.data else None
        user.locked = form.locked.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('Thông tin người dùng đã được cập nhật.')
        return redirect(url_for('admin.users'))
    elif request.method == 'GET':
        form.department.data = user.department_id if user.department_id else 0
        form.parent_user.data = user.parent_id if user.parent_id else 0
    return render_template('admin_user_form.html', form=form, user=user, title='Chỉnh sửa người dùng')


@admin.route('/user/<int:id>/delete', methods=['POST'])
@login_required
@permission_required(Permissions.MANAGE_USERS)
def delete_user(id):
    user_to_delete = User.query.get_or_404(id)

    if any(role.name == 'admin' for role in user_to_delete.roles):
        flash('Không thể xóa người dùng admin.', 'danger')
        return redirect(url_for('admin.users'))

    admin_user = User.query.join(User.roles).filter(Role.name == 'admin').first()
    if not admin_user:
        flash('Không tìm thấy người dùng admin để gán lại dữ liệu.')
        return redirect(url_for('admin.users'))

    # --- PHASE 1: Re-assign foreign keys using bulk updates ---
    try:
        # Re-assign child users
        User.query.filter_by(parent_id=id).update({"parent_id": admin_user.id}, synchronize_session=False)
        
        # Re-assign other related objects
        Patient.query.filter_by(user_id=id).update({"user_id": admin_user.id}, synchronize_session=False)
        pass  # ApprovalRequest removed
        FormSubmission.query.filter_by(user_id=id).update({"user_id": admin_user.id}, synchronize_session=False)
        AuditLog.query.filter_by(user_id=id).update({"user_id": admin_user.id}, synchronize_session=False)
        DynamicForm.query.filter_by(user_id=id).update({"user_id": admin_user.id}, synchronize_session=False)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi gán lại dữ liệu: {e}')
        return redirect(url_for('admin.users'))

    # --- PHASE 2: Log and delete the user in a new transaction ---
    try:
        # Log the deletion
        audit_log = AuditLog(
            user_id=current_user.id,
            action='deleted_user',
            details=f'Đã xóa người dùng {user_to_delete.username} (ID: {id})'
        )
        db.session.add(audit_log)
        
        # Get a fresh copy of the user to delete
        user_to_delete_fresh = User.query.get(id)
        if user_to_delete_fresh:
            db.session.delete(user_to_delete_fresh)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa người dùng: {e}')
        return redirect(url_for('admin.users'))

    flash(f'Đã xóa thành công người dùng "{user_to_delete.username}". Toàn bộ dữ liệu đã được gán lại cho quản trị viên.')
    return redirect(url_for('admin.users'))

@admin.route('/users/bulk-delete', methods=['POST'])
@login_required
@permission_required(Permissions.MANAGE_USERS)
def bulk_delete_users():
    if not current_user.is_admin:
        abort(403)
    
    user_ids = request.form.getlist('user_ids')
    if not user_ids:
        flash('Không có người dùng nào được chọn.', 'warning')
        return redirect(url_for('admin.users'))

    admin_user = User.query.join(User.roles).filter(Role.name == 'admin').first()
    if not admin_user:
        flash('Không tìm thấy người dùng admin để gán lại dữ liệu.', 'danger')
        return redirect(url_for('admin.users'))

    users_to_delete = User.query.filter(User.id.in_(user_ids)).all()
    deleted_count = 0
    errors = []

    for user in users_to_delete:
        if any(role.name == 'admin' for role in user.roles):
            errors.append(f'Không thể xóa người dùng admin: {user.username}.')
            continue

        try:
            # Re-assign related data to admin user
            User.query.filter_by(parent_id=user.id).update({"parent_id": admin_user.id}, synchronize_session=False)
            Patient.query.filter_by(user_id=user.id).update({"user_id": admin_user.id}, synchronize_session=False)
            pass  # ApprovalRequest removed
            FormSubmission.query.filter_by(user_id=user.id).update({"user_id": admin_user.id}, synchronize_session=False)
            AuditLog.query.filter_by(user_id=user.id).update({"user_id": admin_user.id}, synchronize_session=False)
            DynamicForm.query.filter_by(user_id=user.id).update({"user_id": admin_user.id}, synchronize_session=False)

            # Log the deletion
            audit_log = AuditLog(
                user_id=current_user.id,
                action='deleted_user',
                details=f'Đã xóa người dùng {user.username} (ID: {user.id})'
            )
            db.session.add(audit_log)
            
            db.session.delete(user)
            deleted_count += 1
        except Exception as e:
            db.session.rollback()
            errors.append(f'Lỗi khi xóa người dùng {user.username}: {e}')
            # Stop further processing on this user and continue to the next
            continue

    if errors:
        for error in errors:
            flash(error, 'danger')
    
    if deleted_count > 0:
        try:
            db.session.commit()
            flash(f'Đã xóa thành công {deleted_count} người dùng.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi thực hiện xóa: {e}', 'danger')

    return redirect(url_for('admin.users'))

@admin.route('/users/bulk-lock', methods=['POST'])
@login_required
@permission_required(Permissions.MANAGE_USERS)
def bulk_lock_users():
    user_ids = request.form.getlist('user_ids')
    if not user_ids:
        flash('Không có người dùng nào được chọn.', 'warning')
        return redirect(url_for('admin.users'))

    User.query.filter(User.id.in_(user_ids)).update({'locked': True}, synchronize_session=False)
    db.session.commit()
    flash(f'Đã khóa {len(user_ids)} tài khoản.', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/users/bulk-unlock', methods=['POST'])
@login_required
@permission_required(Permissions.MANAGE_USERS)
def bulk_unlock_users():
    user_ids = request.form.getlist('user_ids')
    if not user_ids:
        flash('Không có người dùng nào được chọn.', 'warning')
        return redirect(url_for('admin.users'))

    User.query.filter(User.id.in_(user_ids)).update({'locked': False}, synchronize_session=False)
    db.session.commit()
    flash(f'Đã mở khóa {len(user_ids)} tài khoản.', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    logger.debug("Entering change_password. User: %s", current_user.username)
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.old_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Mật khẩu của bạn đã được thay đổi.', 'success')
            
            # Redirect based on role
            user_roles = [role.name for role in current_user.roles]
            if 'admin' in user_roles:
                return redirect(url_for('admin.dashboard'))
            elif 'staff' in user_roles:
                return redirect(url_for('patient.staff_dashboard'))
            elif 'finance' in user_roles:
                return redirect(url_for('patient.finance_dashboard'))
            else:
                return redirect(url_for('admin.dashboard')) # Fallback
        else:
            flash('Mật khẩu cũ không đúng.', 'danger')
    return render_template('admin/change_password.html', form=form)

@admin.route('/user/<int:id>/reset_password', methods=['POST'])
@login_required
@permission_required(Permissions.MANAGE_USERS)
def reset_password(id):
    user = User.query.get_or_404(id)
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    user.set_password(new_password)
    db.session.commit()
    flash(f'Mật khẩu mới cho người dùng {user.username} là: {new_password}', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/departments', methods=['GET', 'POST'])
@login_required
@permission_required(Permissions.MANAGE_USERS)
def departments():
    form = DepartmentForm()
    if form.validate_on_submit():
        existing_department = Department.query.filter_by(name=form.name.data).first()
        if existing_department:
            flash('Khoa đã tồn tại.', 'warning')
        else:
            department = Department(name=form.name.data)
            db.session.add(department)
            db.session.commit()
            flash('Khoa đã được tạo.', 'success')
        return redirect(url_for('admin.departments'))
    departments = Department.query.all()
    return render_template('admin/departments.html', form=form, departments=departments)

@admin.route('/departments/bulk_update', methods=['POST'])
@login_required
@permission_required(Permissions.MANAGE_USERS)
def bulk_update_departments():
    if 'file' not in request.files:
        flash('Không có phần tệp.', 'danger')
        return redirect(url_for('admin.departments'))
    file = request.files['file']
    if file.filename == '':
        flash('Không có tệp nào được chọn.', 'danger')
        return redirect(url_for('admin.departments'))
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('Loại tệp không hợp lệ.', 'danger')
        return redirect(url_for('admin.departments'))
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file)
        sheet = wb.active
        created_count = 0
        exists_count = 0
        errors = []
        for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 1):
            if not any(row):
                continue
            department_name = str(row[0]).strip() if row[0] else None
            if not department_name:
                errors.append(f'Hàng {i} không có tên khoa.')
                continue
            
            existing_department = Department.query.filter_by(name=department_name).first()
            if existing_department:
                exists_count += 1
                continue
                
            department = Department(name=department_name)
            db.session.add(department)
            created_count += 1
            
        db.session.commit()
        flash(f'Đã tạo mới {created_count} khoa. ({exists_count} khoa đã tồn tại trước đó)', 'success')
        if errors:
            for error in errors:
                flash(error, 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Đã xảy ra lỗi trong quá trình xử lý tệp: {e}', 'danger')
    return redirect(url_for('admin.departments'))

@admin.route('/departments/download_template')
@login_required
def download_department_template():
    import openpyxl
    from io import BytesIO
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Department Template"
    ws.append(["Tên khoa"])
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="department_template.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@admin.route('/department/<int:id>/delete', methods=['POST'])
@login_required
@permission_required(Permissions.MANAGE_USERS)
def delete_department(id):
    department = Department.query.get_or_404(id)
    db.session.delete(department)
    db.session.commit()
    flash('Khoa đã được xóa.', 'success')
    return redirect(url_for('admin.departments'))


@admin.route('/departments/bulk-delete', methods=['POST'])
@login_required
@permission_required(Permissions.MANAGE_USERS)
def bulk_delete_departments():
    department_ids = request.form.getlist('department_ids')
    if not department_ids:
        flash('Không có khoa nào được chọn.', 'warning')
        return redirect(url_for('admin.departments'))

    try:
        Department.query.filter(Department.id.in_(department_ids)).delete(synchronize_session=False)
        db.session.commit()
        flash(f'Đã xóa thành công {len(department_ids)} khoa.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa khoa: {e}', 'danger')

    return redirect(url_for('admin.departments'))

@admin.route('/users/bulk_update', methods=['POST'])
@login_required
@permission_required(Permissions.MANAGE_USERS)
def bulk_update_users():
    # Ensure a clean session starting point
    db.session.rollback()
    
    if 'file' not in request.files:
        flash('Không có phần tệp.', 'danger')
        return redirect(url_for('admin.users'))
    file = request.files['file']
    if file.filename == '':
        flash('Không có tệp nào được chọn.', 'danger')
        return redirect(url_for('admin.users'))
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('Loại tệp không hợp lệ. Vui lòng tải lên file Excel.', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        logger.info("Bắt đầu xử lý tệp Excel cập nhật người dùng...")
        import openpyxl
        # Dùng data_only=True để lấy giá trị tính toán, read_only=True để tối ưu tốc độ đọc
        wb = openpyxl.load_workbook(file, data_only=True)
        sheet = wb.active
        
        # Tải trước dữ liệu để tăng tốc độ so khớp
        all_users = {u.username: u for u in User.query.all()}
        all_depts = {d.name.lower(): d for d in Department.query.all()}
        all_roles = {r.name.lower(): r for r in Role.query.all()}
        
        updated_count = 0
        created_count = 0
        errors = []
        
        for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 1):
            if not row or not any(row):
                continue
            
            # Lấy dữ liệu theo cột (A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7)
            username = str(row[0]).strip() if len(row) > 0 and row[0] else None
            
            # Bỏ qua các hàng không có tên đăng nhập (hàng ma/hàng trống)
            if not username:
                continue
                
            full_name = str(row[1]).strip() if len(row) > 1 and row[1] else None
            email = str(row[2]).strip() if len(row) > 2 and row[2] else None
            role_name = str(row[3]).strip().lower() if len(row) > 3 and row[3] else None
            dept_name = str(row[4]).strip() if len(row) > 4 and row[4] else None
            parent_username = str(row[5]).strip() if len(row) > 5 and row[5] else None
            locked_val = row[6] if len(row) > 6 else None
            password = str(row[7]).strip() if len(row) > 7 and row[7] else None

            if not full_name or not role_name:
                errors.append(f'Hàng {i + 1}: Thiếu Họ tên hoặc Vai trò.')
                continue

            # Xử lý vai trò từ cache
            role_obj = all_roles.get(role_name)
            if not role_obj:
                errors.append(f'Hàng {i + 1}: Vai trò "{role_name}" không hợp lệ.')
                continue

            # Xử lý phòng ban từ cache hoặc tạo mới
            dept = None
            if dept_name:
                lname = dept_name.lower()
                dept = all_depts.get(lname)
                if not dept:
                    logger.info(f"Đang tạo mới khoa: {dept_name}")
                    dept = Department(name=dept_name)
                    db.session.add(dept)
                    db.session.flush()
                    all_depts[lname] = dept

            # Xử lý trạng thái khóa
            if isinstance(locked_val, bool):
                locked = locked_val
            elif locked_val is None:
                locked = False
            else:
                l_str = str(locked_val).strip().lower()
                locked = l_str in ['true', '1', 'yes', 'có', 'đúng', 'x']

            user = all_users.get(username)
            if user:
                # Cập nhật người dùng hiện tại
                user.full_name = full_name
                user.email = email
                user.locked = locked
                user.department_id = dept.id if dept else None
                
                # Cập nhật vai trò nếu thay đổi
                if role_obj not in user.roles:
                    for r in user.roles.all():
                        user.roles.remove(r)
                    user.roles.append(role_obj)
                
                if parent_username:
                    parent = all_users.get(parent_username)
                    user.parent_id = parent.id if parent else None
                
                if password:
                    user.set_password(password)
                
                updated_count += 1
            else:
                # Tạo người dùng mới
                parent = all_users.get(parent_username) if parent_username else None
                user = User(
                    username=username,
                    full_name=full_name,
                    email=email,
                    department_id=dept.id if dept else None,
                    parent_id=parent.id if parent else None,
                    locked=locked
                )
                user.roles.append(role_obj)
                # Mật khẩu mặc định nếu không có trong Excel
                user.set_password(password if password else '123456')
                db.session.add(user)
                all_users[username] = user
                created_count += 1

            if i % 20 == 0:
                logger.info(f"Đã xử lý xong {i} dòng...")

        db.session.commit()
        logger.info(f"Hoàn thành cập nhật hàng loạt: {updated_count} cập nhật, {created_count} tạo mới.")
        flash(f'Thành công: Cập nhật {updated_count} và tạo mới {created_count} người dùng.', 'success')
        if errors:
            for error in errors:
                flash(error, 'warning')
                
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi xử lý tệp Excel: {e}', 'danger')
        logger.error(f"Excel import error: {e}", exc_info=True)
        
    return redirect(url_for('admin.users'))