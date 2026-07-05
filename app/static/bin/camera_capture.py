import cv2
import sys
import argparse
import os
import time

# Suppress OpenCV warnings
os.environ["OPENCV_LOG_LEVEL"] = "OFF"
os.environ["OPENCV_VIDEOIO_LOG_LEVEL"] = "OFF"

def find_available_cameras():
    """Scan and return list of working (index, backend) pairs."""
    backends = [
        (cv2.CAP_DSHOW,  "DirectShow"),
        (cv2.CAP_MSMF,   "Media Foundation"),
        (cv2.CAP_ANY,    "Auto"),
    ]
    found = []
    seen = set()

    for backend, backend_name in backends:
        for i in range(10):  # Try indices 0-9
            try:
                temp_cap = cv2.VideoCapture(i, backend)
                if not temp_cap.isOpened():
                    temp_cap.release()
                    continue
                time.sleep(0.3)
                ret, frame = temp_cap.read()
                temp_cap.release()
                if ret and frame is not None:
                    key = (i, backend)
                    if key not in seen:
                        seen.add(key)
                        found.append((i, backend, backend_name))
            except Exception:
                continue

    return found

def capture_camera(output_path):
    print("INFO:Scanning for available cameras...", flush=True)
    cameras = find_available_cameras()

    if not cameras:
        print(
            "ERROR:Could not open camera. No working device found at indices 0-9 "
            "(tried DirectShow, Media Foundation, Auto backends). "
            "Please check: 1) Camera is not in use by another app (Zoom, Teams, Zalo...). "
            "2) Windows Privacy Settings allow desktop apps to access the Camera.",
            flush=True
        )
        return

    # Use the first working camera found
    cam_index, cam_backend, cam_backend_name = cameras[0]
    print(f"INFO:Opening camera index={cam_index} backend={cam_backend_name}", flush=True)

    cap = cv2.VideoCapture(cam_index, cam_backend)
    if not cap.isOpened():
        print(f"ERROR:Camera index={cam_index} was detected but could not be reopened.", flush=True)
        return

    # Set a reasonable resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    window_name = "Chup anh tu Camera - [ENTER]: Chup, [ESC]: Huy"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    # Try to bring window to foreground on Windows
    try:
        from ctypes import windll
        import ctypes
        # Give the window a moment to appear
        time.sleep(0.3)
        hwnd = windll.user32.FindWindowW(None, window_name)
        if hwnd:
            windll.user32.ShowWindow(hwnd, 9)       # SW_RESTORE
            windll.user32.SetForegroundWindow(hwnd)
            windll.user32.BringWindowToTop(hwnd)
    except Exception:
        pass

    captured = False
    consecutive_failures = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            consecutive_failures += 1
            if consecutive_failures >= 30:
                print("ERROR:Failed to grab frame from camera after 30 attempts.", flush=True)
                break
            time.sleep(0.05)
            continue

        consecutive_failures = 0
        cv2.imshow(window_name, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # ENTER — capture
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cv2.imwrite(output_path, frame)
            print(f"SUCCESS:{output_path}", flush=True)
            captured = True
            break
        elif key == 27:  # ESC — cancel
            print("CANCELLED", flush=True)
            break

        # Window closed via [X]
        try:
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                if not captured:
                    print("CANCELLED", flush=True)
                break
        except Exception:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output_path")
    args = parser.parse_args()

    time.sleep(0.2)
    capture_camera(args.output_path)
