FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

EXPOSE 5000

# Bind to 0.0.0.0 so the app is reachable from outside the container
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
