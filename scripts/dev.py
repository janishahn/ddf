import os
import signal
import socket
import subprocess
import sys
import threading
import time


BACKEND_PORT = 8000

COLOR_RESET = "\033[0m"
COLOR_BACKEND = "\033[34m"
COLOR_FRONTEND = "\033[35m"


def ensure_port_available(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            print(f"Port {port} is not available. Stop the process using it and retry.")
            raise SystemExit(1)


def stream_output(prefix: str, color: str, stream) -> None:
    for line in iter(stream.readline, ""):
        if not line:
            break
        print(f"{color}[{prefix}]{COLOR_RESET} {line.rstrip()}", flush=True)


def main() -> None:
    ensure_port_available(BACKEND_PORT)

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--reload",
        "--port",
        str(BACKEND_PORT),
    ]

    frontend_cmd = ["npm", "run", "dev"]

    backend = subprocess.Popen(
        backend_cmd,
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    frontend = subprocess.Popen(
        frontend_cmd,
        cwd=os.path.join(os.getcwd(), "frontend"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )

    threads = [
        threading.Thread(
            target=stream_output,
            args=("backend", COLOR_BACKEND, backend.stdout),
            daemon=True,
        ),
        threading.Thread(
            target=stream_output,
            args=("frontend", COLOR_FRONTEND, frontend.stdout),
            daemon=True,
        ),
    ]

    for thread in threads:
        thread.start()

    try:
        while True:
            backend_code = backend.poll()
            frontend_code = frontend.poll()
            if backend_code is not None or frontend_code is not None:
                if backend_code is not None:
                    print(
                        f"{COLOR_BACKEND}[backend]{COLOR_RESET} exited with code {backend_code}",
                        flush=True,
                    )
                if frontend_code is not None:
                    print(
                        f"{COLOR_FRONTEND}[frontend]{COLOR_RESET} exited with code {frontend_code}",
                        flush=True,
                    )
                break
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("Shutting down dev servers...")
    finally:
        for proc in (backend, frontend):
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        for proc in (backend, frontend):
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass


if __name__ == "__main__":
    main()
