FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create folder for uploads
RUN mkdir -p data

EXPOSE 5000

# Run Gunicorn (Only one worker -- no need for more)
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
