FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat-traditional wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entry point script executable
RUN chmod +x docker-entrypoint.sh

# Expose the port Streamlit runs on
EXPOSE 8501

# Use entrypoint script for initialization
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command (can be overridden)
CMD ["streamlit", "run", "main.py", "--server.address=0.0.0.0"]
