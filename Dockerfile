FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy your entire project into the container first
COPY . .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install -e .

# We leave CMD blank because docker-compose handles it