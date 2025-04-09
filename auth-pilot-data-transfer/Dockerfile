# Use the official Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI application code
COPY . .

# Expose the port FastAPI runs on
EXPOSE 7100

# Command to run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7100"]