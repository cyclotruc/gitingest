ARG MAIN_REPO=/opt/repo
ARG PYSETUP_PATH=/opt/pysetup

# Build stage
#FROM python:3.12-slim AS builder
FROM ubuntu:22.04 AS builder
LABEL maintainer="RILAH"

ARG PYSETUP_PATH

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 LANGUAGE='en_US:en'
ENV PATH="${PATH}:${PYSETUP_PATH}"
ENV DEBIAN_FRONTEND=noninteractive

# Install Basic Linux
RUN apt-get update \
    && apt-get install -q -y --no-install-recommends --fix-missing -o Acquire::http::Pipeline-Depth=0 \
    wget curl ca-certificates git xvfb locales locales-all apt-utils nano build-essential \
    software-properties-common subversion pkg-config httpie gcc

# Basic Python Packages
RUN apt-get install -q -y --no-install-recommends --fix-missing -o Acquire::http::Pipeline-Depth=0 \
    python3-dev python3-llvmlite python3-pip python3-venv python3-tk \
    python3-cachecontrol python3-debian python-is-python3

# RUN apt-get clean
RUN apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Runtime stage
FROM builder AS final

# From Global Variables
ARG MAIN_REPO
ARG PYSETUP_PATH

# Set Python environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYSETUP_PATH=${PYSETUP_PATH}
ENV PENV_ACT=${PYSETUP_PATH}/.venv/bin/activate
ENV PATH="${PATH}:${PYSETUP_PATH}/.venv/bin"
ENV PKG_PATH="${PYSETUP_PATH}/dist"

WORKDIR $PYSETUP_PATH
ADD  . ${PYSETUP_PATH}

# Install Poetry Library and VENV
RUN pip install -U pip poetry \
    && poetry config virtualenvs.path ${PENV_ACT} \
    && poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true --local \
    && poetry install

# Activate environment at session start
RUN echo "source ${PYSETUP_PATH}/.venv/bin/activate" >> ~/.bashrc
ENV PENV_ACT=${PYSETUP_PATH}/.venv/bin/activate

# Create a non-root user
RUN useradd -m -u 1000 appuser
COPY src/ ./

# Change ownership of the application files
#RUN chown -R appuser:appuser $PYSETUP_PATH

# Switch to non-root user
#USER appuser
EXPOSE 8000

SHELL ["/bin/bash", "-c"]
#CMD ["python", "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
