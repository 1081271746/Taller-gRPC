
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./backend/app
COPY proto ./backend/proto

WORKDIR /app/backend/app

EXPOSE 50051 50052 8000
