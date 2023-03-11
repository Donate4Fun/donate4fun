FROM python:3.11.2

#RUN apk --update --no-cache add alpine-sdk libffi-dev rust cargo openssl-dev
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y fonts-ancient-scripts && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip && pip install poetry

WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-root --only main
RUN poetry run playwright install chromium
RUN poetry run playwright install-deps
COPY donate4fun /app/donate4fun
COPY frontend /app/frontend
CMD ["poetry", "run", "donate4fun-cli", "serve"]
