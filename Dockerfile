# syntax = docker/dockerfile:1.2
# the platform flag is required to run on Apple Silicon for now
# https://stackoverflow.com/questions/65612411/forcing-docker-to-use-linux-amd64-platform-by-default-on-macos/69636473#69636473
FROM --platform=linux/amd64 python:3.10-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_HOME='/opt/poetry' \
    POETRY_NO_INTERACTION=1 \
    APP_HOME=/code \
    APP_PORT=8000

# Prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

ENV PYTHONPATH=${PYTHONPATH}:${APP_HOME}

RUN rm -f /etc/apt/apt.conf.d/docker-clean

# Install dependencies & update
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update -y &&  \
    apt-get install -yqq --no-install-recommends  \
    curl python3-dev build-essential libssl-dev libffi-dev cargo &&  \
    curl -sSL https://install.python-poetry.org | python && \
    rm -rf /var/lib/apt/lists/*

WORKDIR $APP_HOME

RUN poetry config virtualenvs.create false

# Add project dependencies file before rest of code for caching
COPY ./poetry.lock ./pyproject.toml $APP_HOME

RUN poetry install --no-ansi

# Adds our application code to the image
COPY . $APP_HOME
RUN chmod +x $APP_HOME/scripts/run_api.sh

EXPOSE $APP_PORT

#ENTRYPOINT ["sh", "scripts/run_api.sh"]
