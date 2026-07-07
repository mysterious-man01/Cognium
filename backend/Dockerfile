FROM python:3.14-rc-slim-trixie
WORKDIR /usr/local/app

copy requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

copy app .

RUN useradd app
USER app

CMD ["fastapi" "run" "routes.py"]