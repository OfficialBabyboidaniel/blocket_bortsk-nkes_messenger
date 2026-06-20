FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir httpx

COPY blocket_monitor.py .

# Data directory for seen.json and log
RUN mkdir -p /data

ENV DATA_DIR=/data

CMD ["python", "-u", "blocket_monitor.py"]
