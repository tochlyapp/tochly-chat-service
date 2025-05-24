FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .
COPY wait-for-it.sh ./wait-for-it.sh

RUN chmod +x ./wait-for-it.sh

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8001

# Run the server
CMD ["./wait-for-it.sh", "redis:6379", "--timeout=60", "--strict", "--", \
     "./wait-for-it.sh", "cassandra:9042", "--timeout=1000", "--strict", "--", \
     "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]