"""
Patient blueprint - index route.
Cac route chinh duoc tach thanh:
  - submission_routes.py  : dien/xem/sua/xoa phieu
  - dashboard_routes.py   : staff/finance dashboard, API polling
  - form_mgmt_routes.py   : CRUD bieu mau dong va truong
"""
from flask import redirect, url_for
from flask_login import login_required

from app.patient import patient_bp


@patient_bp.route('/')
@login_required
def index():
    return redirect(url_for('patient.staff_dashboard'))
