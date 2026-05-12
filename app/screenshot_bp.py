import os
import subprocess
import uuid
import json
import sys
from flask import Blueprint, jsonify, current_app, send_file, request
from flask_login import login_required

try:
    import win32gui
    import win32process
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False

screenshot_bp = Blueprint('screenshot', __name__)

@screenshot_bp.route('/api/screenshot/list_windows', methods=['GET'])
@login_required
def list_windows():
    if not HAS_PYWIN32:
        return jsonify({'status': 'error', 'message': 'pywin32 not installed'}), 500
    
    windows = []
    def enum_windows_callback(hwnd, _):
        # Filter for "real" application windows
        if not win32gui.IsWindowVisible(hwnd):
            return True
        
        # Must have a title
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return True
            
        # Should not have a parent (it's a top-level task)
        if win32gui.GetParent(hwnd) != 0:
            return True

        # Exclude specific system windows
        if title in ['Settings', 'Microsoft Text Input Application', 'Program Manager', 'Start']:
            return True
        
        # Exclude this browser window (optional, but good for UX)
        # We don't have the browser HWND here easily, but we can filter by title if we know it.
        
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            windows.append({
                'hwnd': hwnd,
                'title': title,
                'pid': pid
            })
        except:
            pass
        return True
    
    try:
        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    # Sort by title
    windows.sort(key=lambda x: x['title'].lower())
    
    # Return only the most relevant windows
    return jsonify({
        'status': 'success', 
        'windows': windows[:40] 
    })


@screenshot_bp.route('/api/screenshot/native_capture', methods=['POST'])
@login_required
def native_capture():
    data = request.json or {}
    hwnd = data.get('hwnd')
    mode = data.get('mode', 'region')
    
    output_filename = f"native_capture_{uuid.uuid4().hex}.png"
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_captures')
    os.makedirs(upload_dir, exist_ok=True)
    output_path = os.path.join(upload_dir, output_filename)
    
    script_path = os.path.join(current_app.root_path, 'static', 'bin', 'clipper.py')
    
    # Use sys.executable to avoid re-locating python and ensure same environment
    cmd = [sys.executable, script_path, output_path, '--mode', mode]
    if hwnd:
        cmd.extend(['--hwnd', str(hwnd)])
    
    try:
        # Optimization for background/hidden processes:
        startupinfo = None
        creationflags = 0
        if os.name == 'nt':
            import win32con
            import win32process
            creationflags = win32process.HIGH_PRIORITY_CLASS
            startupinfo = subprocess.STARTUPINFO()
            # DO NOT use SW_HIDE as it hides the Tkinter selection overlay
            # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            # startupinfo.wShowWindow = win32con.SW_HIDE
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            startupinfo=startupinfo,
            creationflags=creationflags
        )
        
        if "SUCCESS" in result.stdout:
            # PERFORM SERVER-SIDE OCR (Optional)
            ocr_data = {}
            if data.get('perform_ocr', True):
                from .extensions import ocr_reader
                if ocr_reader:
                    try:
                        # Read text from image
                        results = ocr_reader.readtext(output_path, detail=0)
                        full_text = " ".join(results)
                        ocr_data = extract_patient_data(full_text)
                    except Exception as ocr_err:
                        print(f"OCR Error: {ocr_err}")
            
            return jsonify({
                'status': 'success',
                'filename': output_filename,
                'url': f'/api/screenshot/get_capture/{output_filename}',
                'ocr_data': ocr_data
            })
        elif "CANCELLED" in result.stdout:
            return jsonify({'status': 'cancelled'})
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            print(f"SCREENSHOT ERROR: {error_msg}")
            return jsonify({'status': 'error', 'message': error_msg}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

def extract_patient_data(text):
    """Map OCR text to patient fields."""
    import re
    data = {}
    mappings = [
        {'regex': r'(?:Mã bệnh án|Mã BN|Mã bệnh nhân):?\s*(\d+)', 'key': 'Mã bệnh nhân'},
        {'regex': r'(?:Họ tên|Tên bệnh nhân|Họ và tên):?\s*([^\n\r,;]*)', 'key': 'Tên bệnh nhân'},
        {'regex': r'(?:Năm sinh|Ngày sinh):?\s*(\d{2}[/-]\d{2}[/-]\d{4}|\d{4})', 'key': 'Năm sinh'},
        {'regex': r'(?:Giới tính):?\s*(Nam|Nữ)', 'key': 'Giới tính'}
    ]
    for m in mappings:
        match = re.search(m['regex'], text, re.IGNORECASE)
        if match:
            data[m['key']] = match.group(1).strip()
    return data

@screenshot_bp.route('/api/screenshot/extract_data', methods=['POST'])
@login_required
def extract_data_api():
    data = request.json or {}
    text = data.get('text', '')
    if not text:
        return jsonify({'status': 'error', 'message': 'No text provided'}), 400
    
    ocr_data = extract_patient_data(text)
    return jsonify({
        'status': 'success',
        'ocr_data': ocr_data
    })


@screenshot_bp.route('/api/screenshot/get_capture/<filename>')
@login_required
def get_capture(filename):
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_captures')
    file_path = os.path.join(upload_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='image/png')
    return "File not found", 404

