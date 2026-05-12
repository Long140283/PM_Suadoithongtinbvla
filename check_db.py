import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import Permission
import sqlalchemy

app = create_app()
with app.app_context():
    inspector = sqlalchemy.inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('permission')]
    print(f"Columns in 'permission' table: {columns}")
    
    p = Permission.query.filter_by(name='bypass_financial_approval').first()
    if p:
        print(f"Permission: {p.name}")
        print(f"Display Name: {p.display_name}")
        print(f"Hidden: {p.hidden}")
    else:
        print("Permission 'bypass_financial_approval' not found.")
