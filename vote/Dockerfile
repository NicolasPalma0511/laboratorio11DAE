# Define a base stage that uses the official python runtime base image
FROM python:3.11-slim AS base

# Install curl and required libraries for pyodbc
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl unixodbc unixodbc-dev libodbc1 odbcinst apt-transport-https gnupg && \
    # Add the Microsoft repository key and list
    curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc && \
    curl https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    # Install the Microsoft ODBC Driver for SQL Server
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

# Set the application directory
WORKDIR /usr/local/app

# Copy requirements and install dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define a development stage with watchdog installed
FROM base AS dev
RUN pip install watchdog
ENV FLASK_ENV=development
CMD ["python", "app.py"]

# Define the final production stage
FROM base AS final

# Copy the application code
COPY . .

# Expose port 80
EXPOSE 80

# Run the application using Gunicorn
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:80", "--log-file", "-", "--access-logfile", "-", "--workers", "4", "--keep-alive", "0"]
