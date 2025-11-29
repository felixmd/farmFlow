FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for Cloud Run
EXPOSE 8080

# Command to run the bot (will be overridden by specific start commands if needed)
# Using python directly for now, but gunicorn is recommended for webhooks
CMD ["python", "telegram_bot.py"]
