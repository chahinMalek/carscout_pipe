FROM apache/airflow:2.9.3

# Switch to root to install system deps if needed
USER root

# Install runtime dependencies including Chrome and ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Copy app code
COPY . /opt/app

# Install your app
RUN pip install --no-cache-dir /opt/app
