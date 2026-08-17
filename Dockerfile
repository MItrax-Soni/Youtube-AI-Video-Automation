FROM python:3.11-slim

# Install system dependencies (ffmpeg is required for video assembly)
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the requirements file first for better caching
COPY backend/requirements.txt ./backend/

# Install python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the entire project
COPY . .

# Ensure start script is executable
RUN chmod +x start.sh

# Expose port (default FastAPI port)
EXPOSE 8000

# Set environment variable to indicate Railway deployment
ENV RAILWAY_ENVIRONMENT=production

# Start both worker and API using the entrypoint script
CMD ["./start.sh"]
