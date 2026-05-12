import pandas as pd
import os

file_path = 'app/static/docs/user_update_template.xlsx'
os.makedirs(os.path.dirname(file_path), exist_ok=True)

df = pd.DataFrame({
    'Tên đăng nhập': ['user_mau_1', 'user_mau_2'],
    'Họ và tên': ['Nguyễn Văn A', ''],
    'Email': ['nguyenvana@example.com', ''],
    'Vai trò': ['staff', 'finance'],
    'Khoa': ['Khoa Dược', 'Khoa Tim Mạch'],
    'Người dùng cha': ['', ''],
    'Khóa': ['False', 'False']
})

df.to_excel(file_path, index=False)

print(f"Template file created at {file_path}")