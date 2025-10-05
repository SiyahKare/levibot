# ---- build stage ----
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install --upgrade pip
COPY backend/requirements.txt .
RUN pip wheel --wheel-dir=/wheels -r requirements.txt

# ---- runtime ----
FROM python:3.12-slim
WORKDIR /app
ENV TZ=Europe/Istanbul PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /wheels
COPY backend/requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt
COPY backend/ ./backend/
EXPOSE 8000
CMD ["uvicorn", "backend.src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
