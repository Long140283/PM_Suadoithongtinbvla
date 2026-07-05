"""
show_qr.pyw
-----------
Chay khi Windows khoi dong (dat shortcut vao Startup folder).
Doc thong tin tu server_info.txt (do run_service.py ghi ra),
roi hien popup QR de dien thoai quet.

Dung .pyw de chay khong co cua so console (an hoan toan).
"""
import os
import sys
import time
import tkinter as tk

# --- Duong dan ---
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
INFO_FILE = os.path.join(BASE_DIR, 'server_info.txt')

# Cho toi da 60 giay de service khoi dong va ghi file
MAX_WAIT = 60
INTERVAL = 2


def _wait_for_info():
    """Cho den khi server_info.txt xuat hien."""
    waited = 0
    while waited < MAX_WAIT:
        if os.path.exists(INFO_FILE):
            return True
        time.sleep(INTERVAL)
        waited += INTERVAL
    return False


def _read_info():
    info = {}
    try:
        with open(INFO_FILE, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    k, v = line.split('=', 1)
                    info[k.strip()] = v.strip()
    except Exception:
        pass
    return info


def _make_qr_image(url):
    import qrcode
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color='black', back_color='white')


def show_popup(url, hostname, port):
    try:
        from PIL import ImageTk
        img     = _make_qr_image(url)
        has_pil = True
    except Exception:
        has_pil = False

    BG     = '#1a3a6b'
    FG     = '#ffffff'
    ACCENT = '#4a90d9'
    WHITE  = '#ffffff'

    root = tk.Tk()
    root.title('QR - Truy cập từ điện thoại')
    root.resizable(False, False)
    root.attributes('-topmost', True)
    root.configure(bg=BG)

    # --- Tieu de ---
    tk.Label(
        root,
        text='🏥  Bệnh viện Đa khoa Long An',
        font=('Segoe UI', 13, 'bold'),
        bg=BG, fg=FG,
        pady=10,
    ).pack(fill='x')

    tk.Label(
        root,
        text='Quét QR bằng điện thoại để truy cập',
        font=('Segoe UI', 10),
        bg=BG, fg=ACCENT,
    ).pack()

    # --- Anh QR ---
    frame_qr = tk.Frame(root, bg=WHITE, padx=8, pady=8)
    frame_qr.pack(padx=20, pady=12)

    if has_pil:
        tk_img = ImageTk.PhotoImage(img)
        lbl    = tk.Label(frame_qr, image=tk_img, bg=WHITE)
        lbl.image = tk_img  # giu tham chieu
        lbl.pack()
    else:
        # Fallback: hien URL neu khong co Pillow
        tk.Label(
            frame_qr,
            text=url,
            font=('Consolas', 11),
            bg=WHITE, fg='black',
            padx=10, pady=20,
        ).pack()

    # --- Thong tin IP ---
    tk.Label(
        root,
        text=f'Máy chủ: {hostname}   |   Cổng: {port}',
        font=('Segoe UI', 9),
        bg=BG, fg=FG,
        pady=2,
    ).pack()

    tk.Label(
        root,
        text=url,
        font=('Segoe UI', 9, 'underline'),
        bg=BG, fg=ACCENT,
        pady=2,
        cursor='hand2',
    ).pack()

    # --- Nut dong ---
    tk.Button(
        root,
        text='  Đóng  ',
        font=('Segoe UI', 10),
        bg=ACCENT, fg=FG,
        relief='flat',
        padx=20, pady=6,
        cursor='hand2',
        command=root.destroy,
        activebackground='#357abd',
        activeforeground=FG,
    ).pack(pady=(8, 16))

    # Can giua man hinh
    root.update_idletasks()
    w  = root.winfo_reqwidth()
    h  = root.winfo_reqheight()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')

    root.mainloop()


if __name__ == '__main__':
    if not _wait_for_info():
        sys.exit(0)

    info     = _read_info()
    url      = info.get('url',      'http://localhost:8001')
    hostname = info.get('hostname', 'SDTTBV')
    port     = info.get('port',     '8001')

    show_popup(url, hostname, port)
