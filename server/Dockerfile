FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir grpcio grpcio-tools psycopg2-binary yfinance prometheus_client
EXPOSE 50051
CMD ["python", "server.py"]