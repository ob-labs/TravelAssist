FROM python:3.10-slim AS builder

WORKDIR /app

# Specify uv version for reproducibility
ENV UV_VERSION=0.8.9
RUN pip install --no-cache-dir uv==${UV_VERSION}
# If you are in China, uncomment the line below for faster download:
# RUN pip install --no-cache-dir uv==${UV_VERSION} -i https://pypi.tuna.tsinghua.edu.cn/simple

# If you are in China, uncomment to use Aliyun mirror for apt packages:
# RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# If you are in China, uncomment to use Aliyun PyPI mirror:
# ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV UV_HTTP_TIMEOUT=300
RUN uv sync --no-dev

# ==================== Runtime Stage ====================
FROM python:3.10-slim

WORKDIR /app

# If you are in China, uncomment to use Aliyun mirror:
# RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY src ./src

# Create necessary directories
RUN mkdir -p /app/data/uploads /app/logs

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "--server.address=0.0.0.0", "src/ui.py"]
