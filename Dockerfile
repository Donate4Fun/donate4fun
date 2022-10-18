FROM python:3.10.6-alpine

RUN apk --update --no-cache add alpine-sdk libffi-dev rust cargo openssl-dev
RUN pip install --upgrade pip && pip install poetry

WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN poetry install
COPY donate4fun /app/donate4fun
COPY frontend /app/frontend
CMD ["poetry", "run", "python", "-m", "donate4fun"]
