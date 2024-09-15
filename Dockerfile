FROM python:3.9.10-slim-buster

ARG DJANGO_ENV

ENV DJANGO_ENV=${DJANGO_ENV} \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  # pip:
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # poetry:
  POETRY_VERSION=1.4.1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry'

# System deps:
RUN apt-get update && \
  apt-get install --no-install-recommends -y \
  bash \
  build-essential \
  curl \
  gettext \
  git \
  wget \
  # Cleaning cache:
  && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/* \
  # Installing `poetry` package manager:
  # https://github.com/python-poetry/poetry
  && pip install "poetry==$POETRY_VERSION" && poetry --version

# Copy only requirements, to cache them in docker layer
WORKDIR /code
COPY ./poetry.lock ./pyproject.toml /code/

# Project initialization:
RUN echo "$DJANGO_ENV" \
  && poetry install \
  $(if [ "$DJANGO_ENV" = 'Production' ]; then echo '--no-dev'; fi) \
  --no-interaction --no-ansi \
  # Cleaning poetry installation's cache for production:
  && if [ "$DJANGO_ENV" = 'Production' ]; then rm -rf "$POETRY_CACHE_DIR"; fi

# Creating folders, and files for a project:
COPY . /code

COPY ./start-web.sh /start-web.sh

# Setting up proper permissions:
RUN chmod +x /start-web.sh \
  && mkdir -p /code/media /code/static \
  && chmod +x /code/media/ /code/static/
