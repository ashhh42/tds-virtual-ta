# ✅ Use Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all code to container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port required by Render
EXPOSE 10000

# Start the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
