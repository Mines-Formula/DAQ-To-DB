# Use a lightweight Python base image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Poetry
RUN pip install --no-cache-dir poetry

# Set the working directory
WORKDIR /app

# Copy only dependency files first (for better caching)
COPY pyproject.toml poetry.lock ./

RUN apt-get update && apt-get install -y git golang-go

# Clone influx CLI repo and checkout the commit
COPY influx /usr/local/bin/influx
RUN chmod +x /usr/local/bin/influx

# Configure Poetry to not create virtualenvs (run in system environment)
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the project
COPY . .

# Create data directory (in case app writes files)
RUN mkdir -p app/data

# Expose Flask/Gunicorn port
EXPOSE 6969

# Default command to run the app with Gunicorn
CMD ["flask", "--app", "src.app.app:app", "run", "-p", "6969", "-h", "0.0.0.0"]
#CMD ["gunicorn", "-w", "1", "--log-level", "debug", "-b", "0.0.0.0:6969", "src.app.app:app"]
