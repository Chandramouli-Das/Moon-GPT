import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# === CONFIG ===
FASTAPI_HOST = "127.0.0.1"
FASTAPI_PORT = 8000
FRONTEND_PORT = 3000
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

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


def _wait_for_server(process, host: str, port: int, timeout: float) -> bool:
    """Wait until a child opens its port, or return early if it exits."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        if not _is_port_free(host, port):
            return True
        time.sleep(0.25)
    return False


if __name__ == "__main__":
    # Resolve free ports up front (avoids 'port not available' surprises).
    fastapi_port = _find_free_port(FASTAPI_HOST, FASTAPI_PORT)
    frontend_port = _find_free_port(FASTAPI_HOST, FRONTEND_PORT)

    backend_url = f"http://{FASTAPI_HOST}:{fastapi_port}/api/chat"

    # Ensure child processes run inside the same Python environment.
    env = os.environ.copy()
    env["NEXT_PUBLIC_API_URL"] = f"http://{FASTAPI_HOST}:{fastapi_port}"

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
    frontend_cmd = [
        "npm",
        "run",
        "dev",
        "--",
        "--hostname",
        FASTAPI_HOST,
        "--port",
        str(frontend_port),
    ]

    if not (FRONTEND_DIR / "node_modules").exists():
        raise RuntimeError(
            "Frontend dependencies are missing. Run `cd frontend && npm install`."
        )

    # Start the UI first. Backend indexing is lazy and a backend failure should
    # not hide the portfolio shell or resume links.
    frontend_process = subprocess.Popen(frontend_cmd, env=env, cwd=FRONTEND_DIR)

    frontend_url = f"http://{FASTAPI_HOST}:{frontend_port}"
    if not _wait_for_server(
        frontend_process, FASTAPI_HOST, frontend_port, timeout=45
    ):
        exit_code = frontend_process.poll()
        if exit_code is None:
            frontend_process.terminate()
            raise RuntimeError(
                "The Next.js frontend did not become ready within 45 seconds."
            )
        raise RuntimeError(f"Next.js exited during startup (code {exit_code}).")

    print(f"Frontend ready: {frontend_url}", flush=True)
    webbrowser.open(frontend_url)

    fastapi_process = subprocess.Popen(fastapi_cmd, env=env)
    if _wait_for_server(fastapi_process, FASTAPI_HOST, fastapi_port, timeout=90):
        print(f"Backend ready:  {backend_url}", flush=True)
    elif fastapi_process.poll() is not None:
        print(
            "Backend failed to start. The frontend is still available; "
            "review the backend error printed above.",
            file=sys.stderr,
            flush=True,
        )
    else:
        print(
            "Backend is still indexing the resume. The frontend remains "
            "available while it finishes.",
            flush=True,
        )

    try:
        backend_failure_reported = fastapi_process.poll() is not None
        while True:
            if frontend_process.poll() is not None:
                break
            if fastapi_process.poll() is not None and not backend_failure_reported:
                print(
                    "Backend stopped. The frontend will stay open so its "
                    "download features and error message remain accessible.",
                    file=sys.stderr,
                    flush=True,
                )
                backend_failure_reported = True
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping MoonGPT...", flush=True)
    finally:
        for proc in (fastapi_process, frontend_process):
            if proc.poll() is None:
                proc.terminate()
