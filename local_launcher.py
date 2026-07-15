"""Windows launcher for the self-contained JCL converter."""

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


HOST = "127.0.0.1"
PORT = int(os.environ.get("JX3_JCL_PORT", "8090"))


def _resource_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base_path / relative_path


def _wait_for_server(timeout: float = 15) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def main() -> None:
    os.environ.setdefault("FORMULATOR_PATH", str(_resource_path("formulator")))

    import uvicorn
    from app.main import app

    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    url = f"http://{HOST}:{PORT}"
    if not _wait_for_server():
        server.should_exit = True
        raise RuntimeError(f"Local service did not start at {url}.")

    print(f"JX3 JCL converter is running at {url}")
    print("Keep this window open while using the converter. Press Ctrl+C to stop.")
    webbrowser.open(url)

    try:
        while server_thread.is_alive():
            server_thread.join(timeout=0.5)
    except KeyboardInterrupt:
        print("Stopping local service...")
        server.should_exit = True
        server_thread.join(timeout=10)


if __name__ == "__main__":
    main()
