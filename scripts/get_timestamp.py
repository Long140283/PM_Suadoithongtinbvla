"""Helper: writes current timestamp to stdout. Used by backup.bat."""
import datetime, sys
print(datetime.datetime.now().strftime("%Y%m%d_%H%M"), end="")
