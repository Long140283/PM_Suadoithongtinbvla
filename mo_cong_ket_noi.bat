@echo off
chcp 65001 >nul
echo ==========================================================
echo        DỌN ĐƯỜNG KẾT NỐI CHO THIẾT BỊ DI ĐỘNG
echo ==========================================================
echo.

:: 1. Thêm quy tắc Firewall cho cổng 8001
echo [*] Đang mở cổng 8001 trên Windows Firewall...
netsh advfirewall firewall add rule name="HIS_App_Port_8001" dir=in action=allow protocol=TCP localport=8001 profile=any status=enable

if %errorlevel% equ 0 (
    echo [OK] Đã mở cổng 8001 thành công!
) else (
    echo [!] LỖI: Vui lòng chạy file này bằng quyền Administrator (Chuột phải -> Run as Administrator).
    pause
    exit /b 1
)

:: 2. Hiển thị địa chỉ IP để người dùng nhập vào điện thoại
echo.
echo ==========================================================
echo  HÃY NHẬP MỘT TRONG CÁC ĐỊA CHỈ SAU VÀO ĐIỆN THOẠI:
echo ==========================================================
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4 Address" /C:"Địa chỉ IPv4"') do (
    set "ip=%%a"
    set "ip=!ip: =!"
    echo    => http://!ip!:8001
)

echo.
echo ==========================================================
echo LƯU Ý: Điện thoại và máy tính PHẢI cùng bắt một mạng Wi-Fi.
echo ==========================================================
echo.
pause
