FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Compose replaces this command with the development server.
CMD ["sh", "-c", "python src/migrate.py && exec gunicorn --chdir src --bind 0.0.0.0:5000 --access-logfile - app:app"]
