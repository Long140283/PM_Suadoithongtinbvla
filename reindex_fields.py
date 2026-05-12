import sys
sys.stdout.reconfigure(encoding='utf-8')
from app import create_app, db
from app.models import FormField, DynamicForm

app = create_app()
with app.app_context():
    forms = DynamicForm.query.all()
    for form in forms:
        fields = FormField.query.filter_by(form_id=form.id).order_by(FormField.order, FormField.id).all()
        for i, field in enumerate(fields):
            field.order = i + 1
        print(f"Re-indexed {len(fields)} fields for form: {form.name}")
    db.session.commit()
    print("Database committed successfully.")
