FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y curl && \
    curl -O https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.7.3-linux-amd64.tar.gz && \
    tar xvzf influxdb2-client-2.7.3-linux-amd64.tar.gz && \
    cp influx /usr/local/bin/ && \
    rm -rf influx* && \
    apt-get clean

WORKDIR /src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 6767

CMD ["flask", "--app", "app.app:app", "run", "-h", "0.0.0.0", "-p", "6767"]
