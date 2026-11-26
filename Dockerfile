# Image of the transfer job: MongoDB + Cassandra -> Elasticsearch
# Python 3.11: cassandra-driver does not support the newest Python versions yet
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Libraries downloaded beforehand on the host (pip download), installed offline
COPY requirements.txt .
COPY wheels/ wheels/
RUN pip install --no-cache-dir --no-index --find-links=wheels -r requirements.txt

COPY src/ src/

CMD ["python", "src/transfer_to_elasticsearch.py"]