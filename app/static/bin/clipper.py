from PIL import ImageGrab
import os
import sys
import time
import argparse
from ctypes import windll, byref, Structure, sizeof, c_int
from ctypes.wintypes import RECT

try:
    import win32gui
    import win32con
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False

# Force DPI Awareness for Windows to fix coordinate mismatch on scaled displays
try:
    windll.shcore.SetProcessDpiAwareness(1) # System DPI aware (safest for Tkinter)
except Exception:
    try:
        windll.user32.SetProcessDPIAware()
    except Exception:
        pass

def get_visible_window_rect(hwnd):
    """Get the actual visible bounds of a window using DWM API."""
    rect = RECT()
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    res = windll.dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, byref(rect), sizeof(rect))
    if res == 0:
        return (rect.left, rect.top, rect.right, rect.bottom)
    # Fallback to standard rect if DWM fails
    return win32gui.GetWindowRect(hwnd)

class Clipper:
    def __init__(self, output_path, mode="region", target_hwnd=None):
        self.output_path = output_path
        self.mode = mode
        self.target_hwnd = target_hwnd
        self.browser_hwnd = None

        if HAS_PYWIN32:
            self.browser_hwnd = win32gui.GetForegroundWindow()
            
            if self.target_hwnd:
                # FOCUS TARGET WINDOW
                try:
                    # Restore if minimized
                    if self.target_hwnd and win32gui.IsWindow(self.target_hwnd):
                        # Restore if minimized
                        if win32gui.IsIconic(self.target_hwnd):
                            win32gui.ShowWindow(self.target_hwnd, win32con.SW_RESTORE)
                        
                        # Bring to front
                        try:
                            win32gui.SetForegroundWindow(self.target_hwnd)
                            win32gui.BringWindowToTop(self.target_hwnd)
                        except Exception as e:
                            print(f"DEBUG: SetForegroundWindow failed: {e}")
                        
                        # Very short wait for OS to render/bring to front
                        time.sleep(0.1) 
                except Exception as e:
                    print(f"DEBUG: Could not focus target: {e}")
            elif self.mode == "region" and self.browser_hwnd and win32gui.IsWindow(self.browser_hwnd):
                # Minimize current browser quickly
                try:
                    win32gui.ShowWindow(self.browser_hwnd, win32con.SW_MINIMIZE)
                    time.sleep(0.1)
                except:
                    pass

        if self.mode == "task" and self.target_hwnd:
            self.capture_task()
        else:
            self.start_region_selection()

    def capture_task(self):
        """Instantly capture the targeted window."""
        try:
            rect = get_visible_window_rect(self.target_hwnd)
            # Ensure window is not empty or off-screen
            if rect[2] - rect[0] > 10 and rect[3] - rect[1] > 10:
                img = ImageGrab.grab(bbox=rect, all_screens=True)
                img.save(self.output_path)
                print(f"SUCCESS:{self.output_path}")
            else:
                print("ERROR:Window too small or invisible")
        except Exception as e:
            print(f"ERROR:{str(e)}")
        
        # Restore browser immediately
        if HAS_PYWIN32 and self.browser_hwnd:
            try:
                win32gui.ShowWindow(self.browser_hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(self.browser_hwnd)
            except:
                pass
        sys.exit(0)

    def start_region_selection(self):
        """Initialize Tkinter overlay for region selection."""
        import tkinter as tk
        self.root = tk.Tk()
        self.root.title("Chụp màn hình")
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        
        self.canvas = tk.Canvas(self.root, cursor="crosshair", bg="grey", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", self.on_cancel)
        self.root.mainloop()

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x+1, self.start_y+1, outline='red', width=2)

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_cancel(self, event=None):
        self.restore_browser()
        self.root.destroy()
        print("CANCELLED")

    def restore_browser(self):
        if HAS_PYWIN32 and self.browser_hwnd:
            win32gui.ShowWindow(self.browser_hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(self.browser_hwnd)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
        x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
        
        self.root.withdraw()
        
        if x2 - x1 > 5 and y2 - y1 > 5:
            # Minimal delay for overlay to disappear
            time.sleep(0.05)
            try:
                # Remove all_screens=True because Tkinter coordinates are relative to primary monitor
                img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                img.save(self.output_path)
                print(f"SUCCESS:{self.output_path}")
            except Exception as e:
                print(f"ERROR:{str(e)}")
        else:
            print("CANCELLED")
            
        self.restore_browser()
        self.root.destroy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output_path")
    parser.add_argument("--mode", choices=["region", "task"], default="region")
    parser.add_argument("--hwnd", type=int, help="Target window HWND")
    args = parser.parse_args()
    
    Clipper(args.output_path, mode=args.mode, target_hwnd=args.hwnd)


