import wmi
import os
import sys

def get_uvicorn_env():
    c = wmi.WMI()
    for process in c.Win32_Process(name="python.exe"):
        if "uvicorn" in process.CommandLine:
            # We can't directly read env vars of another process easily in Python without ctypes or psutil,
            # but we can try to extract from the environment if they exported it in powershell.
            pass

print("Looking for NEON connection string...")
