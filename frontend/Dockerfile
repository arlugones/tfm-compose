FROM python:3.10 as requirements-stage

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.10

WORKDIR /app

COPY --from=requirements-stage /tmp/requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY main.py gunicorn_conf.py ./
COPY assets/ ./assets/
COPY utils/ ./utils/

EXPOSE 80

CMD ["gunicorn", "-b", "0.0.0.0:80", "-c", "gunicorn_conf.py", "--reload", "main:server"]
# CMD ["uvicorn", "main:server", "--host", "0.0.0.0", "--port", "80", "--reload"]
