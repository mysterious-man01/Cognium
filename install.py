import os
import sys
import json
import platform as pl
import shutil
import subprocess
from urllib.request import urlopen, urlretrieve

# Color codes
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"

ROOT = os.path.dirname(os.path.abspath(__file__))

PLATFORM = pl.system().lower()
ARCH = pl.machine() if pl.machine() != 'aarch64' else 'arm64'

# Use corrct file extractor by platform
if PLATFORM == 'windows':
    import zipfile
else:
    import tarfile

# Error messages
def error(msg: str):
    return RED + msg + RESET

# Warning messages
def warning(msg: str):
    return YELLOW + msg + RESET

# Informative messages
def message(msg: str):
    return BLUE + msg + RESET

# Success messages
def success(msg: str):
    return GREEN + msg + RESET

# Check system compatbility
def check_system():
    if PLATFORM not in ('linux', 'windows', 'darwin'):
        raise SystemExit(error(f"Platform {PLATFORM} not supported"))

    if ARCH in ('x86', 'i386', 'arm', 'armhf'):
        raise SystemExit(error("32 bit platforms not supported"))

    if ARCH not in ('AMD64', 'x86_64', 'x64', 'arm64'):
        raise SystemExit(error(f"{ARCH} platform architecture not supported"))

    if PLATFORM in ('linux', 'windows') and ARCH == 'arm64':
        raise SystemExit(error(f"Arm platform not supported for {PLATFORM}"))

    print(f'Platform is {message(PLATFORM)}')
    print(f'Arch is {message(ARCH)}')
    print(f'Python version is {message(pl.python_version())}')

# Create .env file
def create_envfile():
    default = """
    DATA_PATH=''
    DB_HOST='localhost'
    DB_PORT='5432'
    DB_NAME='chat'
    DB_USER='user'
    DB_PASSWORD='password'
    DB_PERSISTANT='true'
    DB_ECHO='false'
    """

    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='UTF-8') as envfile:
            envfile.write(default)

        print(success(".env file created"))
    else:
        print(success(".env file detected"))

# Handles Flutter SDK installation
def install_flutter():
    flutter_link = 'https://storage.googleapis.com/flutter_infra_release/releases/'
    flutter_pkg = ''

    print(message("Installing Flutter SDK..."))

    with urlopen(f'{flutter_link}/releases_{PLATFORM if PLATFORM != 'darwin' else 'macos'}.json') as request:
        data = json.load(request)

    current_hash = data['current_release']['stable']

    for release in data['releases']:
        if release["hash"] != current_hash:
            continue

        if PLATFORM == "darwin":
            if release["dart_sdk_arch"] != ARCH:
                continue

        flutter_pkg = release["archive"]
        break

    if not flutter_pkg:
        raise SystemExit(error("Could not find a package"))

    try:
        urlretrieve(
            flutter_link + flutter_pkg,
            f'flutter.{'zip' if PLATFORM == 'windows' else 'tar.xz'}'
        )
    except Exception as err:
        raise SystemExit(error(f"Could not download Flutter SDK: {err}"))

    print(success("Flutter SDK downloaded"))

    os.makedirs('.flutter', exist_ok=True)

    print(message("Unpacking SDK..."))
    try:
        if PLATFORM == 'windows':
            with zipfile.ZipFile('flutter.zip') as zp:
                zp.extractall('.flutter')
        else:
            with tarfile.open('flutter.tar.xz') as tar:
                tar.extractall('.flutter')
    except Exception as err:
        raise SystemExit(error(f"Could not extract Flutter SDK\nException -> {err}\nAborting installation"))
    finally:
        os.remove(f'flutter.{'zip' if PLATFORM == 'windows' else 'tar.xz'}')

    flutter_exe = (
        ".flutter/flutter/bin/flutter.bat"
        if PLATFORM == "windows"
        else ".flutter/flutter/bin/flutter"
    )

    try:
        print(message("Running Flutter doctor (this may take a few minutes)..."))
        subprocess.run(
            [
                flutter_exe,
                'doctor'
            ],
            check=True
        )
    except Exception as err:
        raise SystemExit(error(f"Error while running Flutter's initial configuration\n{err}"))

    print(success("Flutter SDK installed"))

# Handles Python venv
def handle_venv():
    if not os.path.exists('.venv'):
        try:
            print(message("Creating virtual environment..."))
            subprocess.run(
                [sys.executable, '-m', 'venv', '.venv'],
                check=True
            )
            print(success("Virtual environment created"))
        except subprocess.CalledProcessError:
            raise SystemExit(error("An error ocurred during Python virtual environment configuration. Installation aborted"))
    else:
        c = question_loop("Do you want to reinstall venv? (y/N)")

        if c == 'y':
            print(message("Removing old virtual environment..."))
            shutil.rmtree('.venv')
            print(success(".venv successfully removed"))
            try:
                print(message("Creating new virtual environment..."))
                subprocess.run(
                    [sys.executable, '-m', 'venv', '.venv'],
                    check=True
                )
                print(success("New virtual environment created"))
            except subprocess.CalledProcessError:
                raise SystemExit(error("An error ocurred during Python virtual environment configuration. Installation aborted"))

# Handle backend dependencies
def install_backend_dep():
    python_exe = os.path.join(
        ROOT,
        '.venv'
        'Scripts' if PLATFORM == 'windows' else 'bin',
        'python.exe' if PLATFORM == 'windows' else 'python'
    )
    
    if os.path.exists(python_exe):
        try:
            print(message("Installing backend dependencies..."))
            subprocess.run(
                [
                    python_exe, '-m',
                    'pip', 'install',
                    '--no-cache-dir', '-r',
                    'requirements.txt'
                ],
                cwd='backend',
                check=True
            )
            print(success("Backend dependencies installed"))
        except Exception as err:
            raise SystemExit(error(f"Could not install dependencies -> {err}"))
    else:
        raise SystemExit(error("Python virtual environment not created"))

# Handles Flutter installation
def handle_flutter():
    if not os.path.exists('.flutter/flutter/bin') and shutil.which('flutter') is None:
        print(warning("Flutter not found"))

        c = question_loop("Would you like to install Flutter? (Y/n)")

        if c == 'n':
            print(message("See Flutter's framework for manual installation"))
            raise SystemExit(
                warning("Installation interrupted by user")
            )

        if c in ('', 'y'):
            install_flutter()
    else:
        if os.path.exists('.flutter'):
            c = question_loop("Would you like to reinstall Flutter SDK? (y/N)")

            if c == 'y':
                print(message("Removing old Flutter SDK..."))
                shutil.rmtree('.flutter')
                print(success("Old Flutter SDK successfully removed"))
                install_flutter()
        else:
            c = question_loop("Would you like to install a Flutter's local environment? (S/n)")

            if c in ('', 'y'):
                print(message("Creating Flutter's local environment..."))
                install_flutter()
            else:
                print(warning("Using global Flutter environment"))

# handles frontend dependencies
def install_frontend_dep():
    flutter_exe = os.path.join(
        ROOT,
        '.flutter',
        'flutter',
        'bin',
        'flutter.bat' if PLATFORM == 'windows' else 'flutter'
    )

    if os.path.exists(flutter_exe):
        ...
    elif shutil.which('flutter'):
        flutter_exe = 'flutter'
        print(warning("Installing dependencies on global Flutter SDK"))
    else:
        raise SystemExit(error("Flutter SDK could not be found. Aborting installation"))

    try:
        print(message("Installing frontend dependencies..."))
        subprocess.run(
            [flutter_exe, 'pub', 'get'],
            cwd='frontend',
            check=True
        )
        print(success("Frontend dependencies installed"))
    except Exception as err:
        raise SystemExit(error(f"Could not install frontend dependencies -> {err}"))

def question_loop(quest: str):
    while True:
        c = input(warning(quest)).strip()
        if c in ('', 'N', 'n', 'Y', 'y'):
            return c.lower()

def install():
    check_system()

    if os.getcwd() != ROOT:
        os.chdir(ROOT)

    # Handle Python venv
    handle_venv()

    # create .env file
    create_envfile()

    # Handle backend dependencies
    install_backend_dep()

    # Handle Flutter installation
    handle_flutter()

    # handle frontend dependencies
    install_frontend_dep()

if __name__ == "__main__":
    install()
