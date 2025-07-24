#What each step does:
#1.Picks a minimal Python image.
#2.All commands run in /app.
#3.Installs Python packages without caching wheels.
#4.Brings in your code.
#5.Tells Docker that the container listens on port 5000.
#6.When the container starts, it runs python app.py.

# 1. Base image: slim Python 3.10
FROM python:3.10-slim

# 2. Set working directory
WORKDIR /app

# 3. Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your application code
COPY . .

# 5. Expose port 5000
EXPOSE 5000

# 6. Default command to run your app
CMD ["python", "app.py"]