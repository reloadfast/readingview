# ReadingView - Audiobook Statistics Dashboard
# Multi-stage build for optimized image size

FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Upgrade build tooling to patched versions before installing deps
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application files
COPY . .

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Remove build tooling from base image (not needed at runtime, avoids CVEs)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && rm -rf /usr/local/lib/python3.11/site-packages/pip* \
              /usr/local/lib/python3.11/site-packages/setuptools* \
              /usr/local/lib/python3.11/site-packages/wheel* \
              /usr/local/lib/python3.11/site-packages/_distutils_hack* \
              /usr/local/lib/python3.11/site-packages/pkg_resources* \
              /usr/local/bin/pip* \
              /usr/local/bin/wheel

# Create data directory for SQLite database (separate from Python database/ package)
RUN mkdir -p /app/data

# Expose Streamlit port
EXPOSE 8506

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8506/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8506", "--server.address=0.0.0.0", "--server.headless=true"]
