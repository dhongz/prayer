FROM python:3.12-alpine

WORKDIR /app

COPY pyproject.toml .
COPY backend backend/
RUN pip install --no-cache-dir .
# RUN apk add --no-cache curl postgresql-dev gcc python3-dev musl-dev

WORKDIR /app/backend