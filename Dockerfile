FROM python:3.11-alpine

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./app /app

# Create alembic versions directory
RUN mkdir -p ./alembic/versions

CMD ["python", "main.py"]

