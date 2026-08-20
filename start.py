import os
import time
import socket
import shutil
import signal
import threading
import platform as pl
import subprocess
from dotenv import load_dotenv
from install import check_system, install, success, error, message

ROOT = os.path.dirname(os.path.abspath(__file__))
PLATFORM = pl.system().lower()
ARCH = pl.machine() if pl.machine() != 'aarch64' else 'arm64'

load_dotenv(os.path.join(ROOT, ".env"))

def start_db():
    print(message("Initializing database..."))
    try:
        database = spawn(
            "Database",
            [
                'docker', 'compose', '-f',
                'docker-compose.db.yml', 'up'
            ],
            cwd=ROOT,
        )

        return database
    except Exception as err:
        raise SystemExit(error(f"Could not create database instance: {err}"))

def start_backend(py_exe):
    print(message("Initalizing backend..."))
    try:
        backend = spawn(
            "Backend",
            [py_exe, '-m', 'fastapi', 'run', 'init.py'],
            cwd=os.path.join(ROOT, 'backend', 'app'),
        )

        return backend
    except Exception as err:
        raise SystemExit(error(f"Could not create backend instance: {err}"))

def start_frontend(flutter):
    print(message("Initializing frontend..."))
    local_flutter = os.path.exists(flutter)
    global_flutter = shutil.which('flutter')
    use_global_flutter = False

    if local_flutter:
        use_global_flutter = False
    elif global_flutter:
        use_global_flutter = True
    else:
        raise SystemExit(error('Flutter not found'))

    try:
        frontend = spawn(
            "Frontend",
            [
                'flutter' if use_global_flutter else flutter,
                "run", "-d", "web-server", "--release",
                "--web-hostname", "0.0.0.0", "--web-port", "8080"
            ],
            cwd=os.path.join(ROOT, 'frontend')
        )

        return frontend
    except Exception as err:
        raise SystemExit(error(f"Could not create frontend instance: {err}"))

def spawn(name, args, cwd):
    process = subprocess.Popen(
        args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    threading.Thread(
        target=pipe_reader,
        args=(name, process),
        daemon=True,
    ).start()

    return process

def pipe_reader(name, process):
    for line in process.stdout:
        print(f"[{success(name)}] {line}", end="")

def wait_port(host, port, process, timeout=30):
    start = time.time()

    while time.time() - start < timeout:

        # processo terminou
        if process.poll() is not None:
            raise RuntimeError(
                error(f"Process terminated with code {process.returncode}")
            )

        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.5)

    raise TimeoutError(
        error(f"Timed out waiting for {host}:{port}")
    )

def main():
    check_system()

    database = None
    backend = None
    frontend = None

    if os.getcwd() != ROOT:
        os.chdir(ROOT)

    python_venv = os.path.join(
        ROOT,
        '.venv',
        'Scripts' if PLATFORM == 'windows' else 'bin',
        'python.exe' if PLATFORM == 'windows' else 'python'
    )
    local_flutter = os.path.join(
        ROOT,
        '.flutter',
        'flutter',
        'bin',
        'flutter.bat' if PLATFORM == 'windows' else 'flutter'
    )

    if not os.path.exists(python_venv):
        install()

    if (
        not os.path.exists(local_flutter)
        and shutil.which("flutter") is None
    ):
        install()

    if os.getenv('DB_PERSISTANT', default='false').strip().lower() in ('1', 'y', 'yes', 'true'):
        database = start_db()

        wait_port("127.0.0.1", os.getenv('DB_PORT'), database, timeout=120)

    backend = start_backend(python_venv)

    wait_port('127.0.0.1', 8000, backend)

    frontend = start_frontend(local_flutter)

    print(success("All done"))

    try:
        if database:
            database.wait()

        backend.wait()
        frontend.wait()

    except KeyboardInterrupt:
        print('Keyboard unterruption')

        if PLATFORM == 'windows':
            if frontend:
                frontend.send_signal(signal.CTRL_BREAK_EVENT)

            if backend:
                backend.send_signal(signal.CTRL_BREAK_EVENT)

            if database:
                database.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            if frontend:
                frontend.send_signal(signal.SIGINT)

            if backend:
                backend.send_signal(signal.SIGINT)

            if database:
                database.send_signal(signal.SIGINT)

            os.system("stty sane")

if __name__ == "__main__":
    main()
