import os
import subprocess

scripts_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(scripts_dir)
log_dir = os.path.join(root_dir, "logs")

if os.path.exists(log_dir):
    for filename in os.listdir(log_dir):
        if filename.endswith(".pid"):
            pid_path = os.path.join(log_dir, filename)
            try:
                with open(pid_path, "r") as pf:
                    pid_str = pf.read().strip()
                if pid_str:
                    pid = int(pid_str)
                    print(f"Stopping {filename[:-4]} (PID: {pid})...")
                    # On Windows, taskkill /F /T /PID kills the process and all its children
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"Error stopping PID from {filename}: {e}")
            try:
                os.remove(pid_path)
            except:
                pass

# Also double check ports 8000-8006
ports = [8000, 8001, 8002, 8003, 8004, 8005, 8006]
for port in ports:
    try:
        # Check netstat for lingering PIDs on port and taskkill them
        output = subprocess.check_output(f'netstat -ano | findstr LISTENING | findstr :{port}', shell=True).decode()
        for line in output.strip().split('\n'):
            parts = line.strip().split()
            if len(parts) >= 5:
                pid = parts[-1]
                print(f"Killing process {pid} lingering on port {port}...")
                subprocess.run(["taskkill", "/F", "/T", "/PID", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

print("All processes stopped.")
