import os
from platform import system
import json
from dotenv import load_dotenv

os.chdir(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..' 
))

CONSTRAINT = ('1', 'y', 'yes', 'true')

ROOT = os.path.abspath(os.curdir)

PATH = (os.getenv('DATA_PATH'), os.path.join(ROOT, 'DATA'))

PLATFORM_SLASH = '\\' if system().lower() == 'windows' else '/'

MODELS_PATH = os.path.join(
    PATH[0] if PATH[0] else PATH[1],
    'Models'
)

load_dotenv(os.path.join(ROOT, '.env'))

class DbConfig:
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')

    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')

    DB_PERSISTANT = os.getenv('DB_PERSISTANT', default="true")
    DB_ECHO = os.getenv('DB_ECHO', default="false")

def check_cfg_file():
    data_path = PATH[0] if PATH[0] else PATH[1]

    cfg_path = os.path.join(data_path, 'Config')
    if not os.path.exists(cfg_path):
        os.makedirs(cfg_path, exist_ok=True)

    with open(os.path.join(cfg_path, 'config.json'), 'r', encoding='UTF-8') as cfg_file:
        return json.loads(cfg_file.read())
