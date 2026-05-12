"""
Decorators dung chung cho toan bo ung dung.
Chi dinh nghia permission_required mot lan duy nhat tai day.
"""
import logging
from functools import wraps
from flask import abort, redirect, url_for, flash, request
from flask_login import current_user

logger = logging.getLogger(__name__)


def permission_required(permission_name):
    """
    Decorator kiem tra quyen truy cap.
    Su dung: @permission_required('manage_forms')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if not current_user.has_permission(permission_name, ignore_hidden=True):
                logger.warning(
                    'Permission denied: user=%s permission=%s path=%s',
                    current_user.username, permission_name, request.path
                )
                flash('Bạn không có quyền truy cập trang này. Hệ thống đã tự động đưa bạn về trang chủ phù hợp.', 'warning')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(*role_names):
    """
    Decorator kiem tra vai tro.
    Su dung: @role_required('admin', 'finance')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if not any(current_user.has_role(r) for r in role_names):
                logger.warning(
                    'Role denied: user=%s required=%s path=%s',
                    current_user.username, role_names, request.path
                )
                flash('Bạn không có quyền truy cập trang này. Hệ thống đã tự động đưa bạn về trang chủ phù hợp.', 'warning')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
