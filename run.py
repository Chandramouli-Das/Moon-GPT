import subprocess
import webbrowser
import os
import time
import uvicorn
import multiprocessing

# === CONFIG ===
FASTAPI_HOST = "127.0.0.1"
FASTAPI_PORT = 8000
STREAMLIT_PORT = 8501
STREAMLIT_APP = "streamlit_chat.py"

# === Run FastAPI in a separate PROCESS (not thread)
def start_fastapi():
    uvicorn.run("main:app", host=FASTAPI_HOST, port=FASTAPI_PORT, reload=False)

if __name__ == "__main__":
    # 🔥 Start FastAPI in a separate process without reload=True
    fastapi_process = multiprocessing.Process(target=start_fastapi)
    fastapi_process.start()

    # 🌐 Wait and start Streamlit
    time.sleep(2)
    subprocess.Popen(["streamlit", "run", STREAMLIT_APP, "--server.port", str(STREAMLIT_PORT)])
    webbrowser.open(f"http://localhost:{STREAMLIT_PORT}")

    # ✅ Optional: Wait for both to finish
    fastapi_process.join()