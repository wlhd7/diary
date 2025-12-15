ARG BASE_IMAGE=mirror.ccs.tencentyun.com/library/python:3.11-slim
FROM ${BASE_IMAGE}

# If the mirror isn't accessible in your environment, override at build time:
# docker build --build-arg BASE_IMAGE=python:3.11-slim -t diary .
# or with compose (in `docker-compose.yml` under build.args):
#   build:
#     args:
#       BASE_IMAGE: python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (if any) and pip requirements
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

ENV FLASK_APP=diary:create_app
ENV FLASK_ENV=production

EXPOSE 8000

CMD ["gunicorn", "diary:create_app()", "--bind", "0.0.0.0:8000", "--workers", "3", "--worker-class", "gthread", "--threads", "4"]
