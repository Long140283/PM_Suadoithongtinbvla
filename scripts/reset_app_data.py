import sys
import os
import shutil

# Thêm đường dẫn gốc vào sys.path để có thể import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app import create_app, db
from app.models import Patient, FormSubmission, SubmissionValue, Attachment, AuditLog, User, Department, DynamicForm

def reset_data():
    app = create_app()
    with app.app_context():
        print("\n" + "="*50)
        print("--- DANG BAT DAU DON DEP DU LIEU TRIET DE ---")
        print("="*50)
        
        try:
            # 1. Xóa các bản ghi dữ liệu hoạt động
            print("\n[1] Dang xoa du lieu trong Database...")
            
            # Xóa theo thứ tự để tránh lỗi ràng buộc (Foreign Key)
            count_val = SubmissionValue.query.delete()
            print(f"    - Da xoa {count_val} SubmissionValue.")
            
            count_att = Attachment.query.delete()
            print(f"    - Da xoa {count_att} Attachment.")
            
            count_sub = FormSubmission.query.delete()
            print(f"    - Da xoa {count_sub} FormSubmission.")
            
            count_log = AuditLog.query.delete()
            print(f"    - Da xoa {count_log} AuditLog.")
            
            count_pat = Patient.query.delete()
            print(f"    - Da xoa {count_pat} Patient.")
            
            print("    - Dang xoa cac User (ngoai tru admin)...")
            users_to_delete = User.query.filter(User.username != 'admin').all()
            count_user = 0
            for u in users_to_delete:
                u.roles = []
                u.permissions = []
                db.session.delete(u)
                count_user += 1
            print(f"    - Da xoa {count_user} User.")
            
            count_dept = Department.query.delete()
            print(f"    - Da xoa {count_dept} Department.")
            
            db.session.commit()
            print("[OK] Da hoan tat xoa du lieu trong Database.")
            
            # Tối ưu hóa Database (Thu nhỏ file .db)
            print("\n[2] Dang toi uu hoa Database (VACUUM)...")
            db.session.execute(text("VACUUM"))
            print("[OK] File database da duoc thu nho.")
            
        except Exception as e:
            db.session.rollback()
            print(f"[!] LOI DATABASE: {e}")

        # 3. Xóa các tệp vật lý trong thư mục uploads
        print("\n[3] Dang don dep vung nho luu tru tep tin...")
        upload_root = os.path.join(app.root_path, 'static', 'uploads')
        
        if os.path.exists(upload_root):
            print(f"    - Dang quet thu muc goc: {upload_root}")
            for root, dirs, files in os.walk(upload_root):
                for file in files:
                    if file == '.gitkeep': continue
                    file_path = os.path.join(root, file)
                    try:
                        os.unlink(file_path)
                        # print(f"      [OK] Da xoa: {file}")
                    except Exception as e:
                        print(f"      [!] Khong the xoa file {file}: {e}")
                
                # Không xóa các thư mục con (để giữ cấu trúc), chỉ xóa file bên trong
                # Nếu muốn xóa luôn thư mục rỗng thì dùng os.rmdir(root) sau khi xóa file
            print("[OK] Da xoa toan bo tep tin tai len (signatures, screenshots, attachments).")
        else:
            print("[!] Khong tim thay thu muc uploads.")
        
        print("\n" + "="*50)
        print("--- HOAN THANH: APP DA SAN SANG DE BAN GIAO ---")
        print("="*50)

if __name__ == "__main__":
    reset_data()
