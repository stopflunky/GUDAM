FROM python:3.9-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install confluent-kafka
RUN pip install prometheus_client
COPY . .
CMD ["python", "dataCollector.py"]
