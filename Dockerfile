FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create folder for uploads
RUN mkdir -p data

EXPOSE 6969

# Run Gunicorn (Only one worker -- no need for more)
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:6969", "app:app"]
