FROM apache/airflow:2.9.3-python3.11

USER root

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

USER airflow
WORKDIR /opt/app

COPY . /opt/app

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir .

ENV PYTHONPATH="/opt/app:$PYTHONPATH"
