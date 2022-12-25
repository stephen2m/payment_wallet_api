# syntax = docker/dockerfile:1.2
# the platform flag is required to run on Apple Silicon for now
# https://stackoverflow.com/questions/65612411/forcing-docker-to-use-linux-amd64-platform-by-default-on-macos/69636473#69636473
FROM --platform=linux/amd64 python:3.10-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_CACHE_DIR=/var/cache/buildkit/pip \
    APP_HOME=/code \
    APP_PORT=8000

RUN mkdir -p $PIP_CACHE_DIR
RUN rm -f /etc/apt/apt.conf.d/docker-clean

# Install dependencies & update
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update -y &&  \
    apt-get install -yqq --no-install-recommends  \
    curl python3-dev build-essential libssl-dev libffi-dev cargo &&  \
    rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip \
    && python -m pip install --upgrade poetry \
    && poetry config virtualenvs.create false

WORKDIR $APP_HOME

# Add project dependencies file before rest of code for caching
COPY ./poetry.lock ./pyproject.toml $APP_HOME

ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN poetry install --no-interaction --no-ansi -vvv

# Adds our application code to the image
COPY . $APP_HOME
RUN chmod +x /code/docker/scripts/run_api.sh
RUN chmod +x /code/docker/scripts/run_celery_worker.sh

EXPOSE 80
