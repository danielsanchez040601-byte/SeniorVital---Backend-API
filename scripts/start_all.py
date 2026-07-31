import os
import sys
import subprocess
import time

CREATE_BREAKAWAY_FROM_JOB = 0x01000000
CREATE_NO_WINDOW = 0x08000000
flags = CREATE_BREAKAWAY_FROM_JOB | CREATE_NO_WINDOW

scripts_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(scripts_dir)
log_dir = os.path.join(root_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

# Ensure storage directories exist
os.makedirs(os.path.join(root_dir, "storage", "videos"), exist_ok=True)
os.makedirs(os.path.join(root_dir, "storage", "progress-photos"), exist_ok=True)

python_exe = os.path.join(root_dir, "venv", "Scripts", "python.exe")

services = [
    {"name": "auth-profile", "port": 8001, "dir": "auth-profile-service"},
    {"name": "catalog", "port": 8002, "dir": "catalog-service"},
    {"name": "routines-ai", "port": 8003, "dir": "routines-ai-service"},
    {"name": "tracking", "port": 8004, "dir": "tracking-service"},
    {"name": "dashboard", "port": 8005, "dir": "dashboard-service"},
    {"name": "notification", "port": 8006, "dir": "notification-service"},
    {"name": "gateway", "port": 8000, "dir": "gateway"},
]

for svc in services:
    name = svc["name"]
    port = svc["port"]
    svc_dir = os.path.join(root_dir, svc["dir"])
    
    log_path = os.path.join(log_dir, f"{name}.log")
    err_path = os.path.join(log_dir, f"{name}.err.log")
    pid_path = os.path.join(log_dir, f"{name}.pid")
    
    log_file = open(log_path, "w", encoding="utf-8")
    err_file = open(err_path, "w", encoding="utf-8")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = root_dir + os.pathsep + env.get("PYTHONPATH", "")
    
    # Launch uvicorn
    cmd = [
        python_exe, "-m", "uvicorn", "main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload"
    ]
    
    proc = subprocess.Popen(
        cmd,
        cwd=svc_dir,
        env=env,
        stdout=log_file,
        stderr=err_file,
        creationflags=flags
    )
    
    with open(pid_path, "w") as pf:
        pf.write(str(proc.pid))
        
    print(f"Started {name} on port {port} (PID: {proc.pid})")
    time.sleep(3)

print("All microservices started persistently. Keeping launcher alive.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting launcher...")
