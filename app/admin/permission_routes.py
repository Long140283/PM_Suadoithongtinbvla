"""
Routes quan ly quyen han (Permission / Role).
"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.models import Permission, Role
from app.extensions import db
from app.decorators import permission_required
from app.constants import Permissions
from app.admin.forms import ManagePermissionForm

from . import admin


@admin.route('/permissions', methods=['GET', 'POST'])
@login_required
@permission_required(Permissions.MANAGE_PERMISSIONS)
def manage_permissions():
    form = ManagePermissionForm()
    roles = Role.query.all()
    permissions = Permission.query.all()

    if request.method == 'POST' and form.validate_on_submit():
        for role in roles:
            new_perms = []
            for perm in permissions:
                if f'perm_{role.id}_{perm.id}' in request.form:
                    new_perms.append(perm)
            role.permissions = new_perms

        for perm in permissions:
            perm.hidden = f'hidden_{perm.id}' in request.form

        try:
            db.session.commit()
            flash('Quyen da duoc cap nhat thanh cong.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Loi khi luu thay doi: {e}', 'danger')

        return redirect(url_for('admin.manage_permissions'))

    return render_template(
        'admin/permissions.html',
        roles=roles,
        permissions=permissions,
        permission_translations=Permissions.DISPLAY_NAMES,
        form=form,
    )
