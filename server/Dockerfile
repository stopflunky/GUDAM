FROM python:3.10-slim
WORKDIR /app
COPY server.py /app/
COPY file_pb2.py /app/
COPY file_pb2_grpc.py /app/
RUN pip install --no-cache-dir grpcio grpcio-tools psycopg2-binary yfinance
EXPOSE 50051
CMD ["python", "server.py"]