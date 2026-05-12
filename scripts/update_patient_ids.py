
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Patient, FormSubmission, SubmissionValue, FormField

app = create_app()

def run_update():
    with app.app_context():
        submissions = FormSubmission.query.all()
        for submission in submissions:
            if submission.patient_id is None:
                patient_code_value = None
                for value in submission.values:
                    if value.field.label.lower() == 'mã số bệnh nhân':
                        patient_code_value = value.value
                        break

                if patient_code_value:
                    patient = Patient.query.filter_by(patient_code=patient_code_value).first()
                    if patient:
                        submission.patient_id = patient.id
                        print(f"Updated submission {submission.id} with patient_id {patient.id}")

        db.session.commit()
        print("Finished updating patient_ids for FormSubmissions.")

if __name__ == "__main__":
    run_update()