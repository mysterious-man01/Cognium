import os
from dotenv import load_dotenv
from fastapi import FastAPI

os.chdir(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..',
    '..'
))

ROOT = os.path.abspath(os.curdir)

PATH = (os.getenv('DATA_PATH'), os.path.join(ROOT, 'DATA'))

load_dotenv(os.path.join(ROOT, '.env'))

app = FastAPI()

if __name__ == "__main__":
    pass
