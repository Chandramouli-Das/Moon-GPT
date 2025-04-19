import subprocess
import signal
import sys

def start_backend():
    print("Starting FastAPI backend...")
    # Assuming the FastAPI app is in backend/main.py and the app instance is named "app"
    backend_proc = subprocess.Popen([
        "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"
    ])
    return backend_proc

def start_frontend():
    print("Starting React frontend...")
    # Make sure the frontend folder is in the project root and named "frontend"
    frontend_proc = subprocess.Popen(
        ["npm", "start"],
        cwd="frontend"
    )
    return frontend_proc

if __name__ == "__main__":
    backend_proc = start_backend()
    frontend_proc = start_frontend()

    # Graceful shutdown handler
    def signal_handler(sig, frame):
        print("\nShutting down both backend and frontend...")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Both backend and frontend are running. Press CTRL+C to stop.")
    backend_proc.wait()
    frontend_proc.wait()