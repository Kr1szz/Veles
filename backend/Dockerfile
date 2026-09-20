# Multi-Stage Production Dockerfile for Veles Shield Backend & C++ Engine

# Stage 1: Build C++ Native Anomaly & Entropy Engine
FROM gcc:14-bookworm AS cpp-builder
WORKDIR /build
COPY backend/cpp/ .
RUN make clean && make -j$(nproc)

# Stage 2: Production Python Runtime
FROM python:3.12-slim-bookworm AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/venv/bin:$PATH"

WORKDIR /app

# Install runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libstdc++6 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled C++ shared libraries from Stage 1
COPY --from=cpp-builder /build/libveles.so /usr/local/lib/libveles.so
COPY --from=cpp-builder /build/libaegis.so /usr/local/lib/libaegis.so
RUN ldconfig

# Set up virtual environment and install Python dependencies
RUN python -m venv /venv
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY backend/aegis /app/aegis
COPY frontend/dist /app/frontend/dist

# Security: Run as dedicated non-root user
RUN useradd -u 10001 -m -s /bin/bash velesuser && \
    chown -R velesuser:velesuser /app
USER velesuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "aegis.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--access-log"]
