FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY backend ./backend
COPY domain ./domain
COPY plugins ./plugins

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .[dev]

EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

