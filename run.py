import os
import socket
import subprocess
import sys
import time
import webbrowser

# === CONFIG ===
FASTAPI_HOST = "127.0.0.1"
FASTAPI_PORT = 8000
STREAMLIT_PORT = 8503
STREAMLIT_APP = "streamlit_chat.py"

def _is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.connect_ex((host, port)) != 0


def _find_free_port(host: str, start_port: int, max_tries: int = 20) -> int:
    port = start_port
    for _ in range(max_tries):
        if _is_port_free(host, port):
            return port
        port += 1
    raise RuntimeError(f"No free port found starting at {start_port}")

if __name__ == "__main__":
    # Resolve free ports up front (avoids 'port not available' surprises).
    fastapi_port = _find_free_port(FASTAPI_HOST, FASTAPI_PORT)
    streamlit_port = _find_free_port(FASTAPI_HOST, STREAMLIT_PORT)

    backend_url = f"http://{FASTAPI_HOST}:{fastapi_port}/api/chat"

    # Ensure child processes run inside the same Python environment.
    env = os.environ.copy()
    env["BACKEND_URL"] = backend_url

    fastapi_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        FASTAPI_HOST,
        "--port",
        str(fastapi_port),
    ]
    streamlit_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        STREAMLIT_APP,
        "--server.port",
        str(streamlit_port),
    ]

    fastapi_process = subprocess.Popen(fastapi_cmd, env=env)

    # Give the backend a moment to boot before Streamlit starts calling it.
    time.sleep(2)
    streamlit_process = subprocess.Popen(streamlit_cmd, env=env)

    print(f"Backend:   {backend_url}")
    print(f"Frontend:  http://{FASTAPI_HOST}:{streamlit_port}")
    webbrowser.open(f"http://{FASTAPI_HOST}:{streamlit_port}")

    try:
        # Wait for either process to exit, then stop the other.
        while True:
            if fastapi_process.poll() is not None:
                streamlit_process.terminate()
                break
            if streamlit_process.poll() is not None:
                fastapi_process.terminate()
                break
            time.sleep(0.5)
    finally:
        for proc in (fastapi_process, streamlit_process):
            if proc.poll() is None:
                proc.terminate()
