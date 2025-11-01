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
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:6969", "src.app.app:app"]
