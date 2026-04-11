FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=120

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY src/requirements.txt ./requirements.txt
RUN uv pip install --system -r requirements.txt \
    && uv pip uninstall --system opencv-python \
    && uv pip install --system opencv-python-headless

COPY src/ ./

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
