FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --uid 10001 --home-dir /app appuser
WORKDIR /app

COPY requirements-lock.txt /tmp/requirements-lock.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements-lock.txt

COPY --chown=appuser:appgroup examples/ch12-fastapi-container/app ./app

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
