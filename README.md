# Stitch Wallet Application Example

[![Built with](https://img.shields.io/badge/Built_with-Cookiecutter_Django_Rest-F7B633.svg)](https://github.com/agconti/cookiecutter-django-rest)

Backend API for a basic wallet management system using Stitch LinkPay and Linked disbursements.

# Prerequisites

- [Docker](https://docs.docker.com/get-docker/)

# Local Development

To speed up docker builds, you'll want to ensure [buildkit](https://docs.docker.com/build/buildkit/) is enabled.  
For Linux you can set the `DOCKER_BUILDKIT=1` environment variable or add this to your `daemon.json` e.g. for Windows `"features": { "buildkit": true }`

First step will be to build the API container.  To avoid having the Stitch client ID and secret in the docker compose file, you'll need
to pass those values as build arguments.

```bash
docker build --build-arg STITCH_CLIENT_ID=$STITCH_CLIENT_ID --build-arg STITCH_CLIENT_SECRET=$STITCH_CLIENT_SECRET .
```

Start the dev server on port 8081 for local development:

```bash
docker-compose up
```

Run a command inside the docker container:

```bash
docker-compose run --rm api [command]
```

## Project Dependencies

This project uses poetry to manage any Python packages required at runtime.  To add any new packages, you can run the following command

```bash
poetry add [package]
```

## Migrations

Django's migration mechanisms are used for managing changes to the tables to make DB changes easy.

To generate a migration file (which you'll also commit to the codebase) from changes you've made locally, run the following command:

```bash
docker-compose run --rm api python manage.py makemigrations
```

Then you can apply the migration to the database:

```bash
docker-compose run --rm api python manage.py migrate
```

Then each time the database models change repeat the `makemigrations` and `migrate` commands.

To sync the database in another system just pull the latest changes and run the `migrate` command (for local development, this is always done automatically when Docker is starting up).

## Shell

To open an interactive Python shell, run the following command:

```bash
docker-compose run --rm api python manage.py shell
```

You can also drop into the Linux shell by running the following command:

```bash
docker-compose run --rm api /bin/bash
```

## API Authentication

The API expects each incoming request (except login requests) to have a valid JWT in the `Authorization` header in the 
format `Bearer <your-jwt>`. On a successful login request, the user gets an access and refresh token.  Each access token 
is valid for 1 hour while the refresh token valid for 1 year. The refresh token is to be used to get a new valid access 
token should the current one expire.
