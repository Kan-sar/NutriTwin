FROM python:3.14.5-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml requirements.lock README.md ./
COPY apps ./apps
COPY packages ./packages
COPY services ./services
COPY scripts ./scripts
COPY data/processed ./data/processed
COPY alembic.ini ./

RUN python -m pip install --no-cache-dir -r requirements.lock \
    && python -m pip install --no-cache-dir --no-deps .

EXPOSE 8000
CMD ["uvicorn", "nutritwin_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
