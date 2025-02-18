# Use an official lightweight Python image.
FROM python:3.11-slim

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements file and install dependencies.
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Set environment variables for Flask.
ENV FLASK_APP=src/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development

# Expose port 5000 for the Flask app.
EXPOSE 5000

# Run the Flask application.
CMD ["flask", "run"]
