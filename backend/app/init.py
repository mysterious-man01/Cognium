import os
from fastapi import FastAPI

ROOT = os.path.dirname(os.path.abspath('..'))
PATH = (os.getenv('DATA_PATH'), os.path.join(ROOT, 'DATA'))

app = FastAPI()

if __name__ == "__main__":
    pass
