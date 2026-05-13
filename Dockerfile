FROM python:3.12-slim

# Non-root user for security
RUN useradd --create-home --shell /bin/bash app
WORKDIR /home/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir --no-deps .

USER app

ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import socket; s=socket.create_connection(('localhost',8000),timeout=3); s.close()" || exit 1

CMD ["python", "-m", "kaizen_redmine_mcp"]
