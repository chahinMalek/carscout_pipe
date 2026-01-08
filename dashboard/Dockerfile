FROM python:3.11-slim

WORKDIR /opt/app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . .

RUN uv pip install --system --no-cache .

ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV PYTHONPATH="/opt/app"

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py"]
