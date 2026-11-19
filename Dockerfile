FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The application writes only to the uploads directory, so it does not need root.
RUN useradd --create-home app \
    && mkdir -p /data/uploads \
    && chown app:app /data/uploads
USER app
# pip installs here when the tests add their packages as this user.
ENV PATH="/home/app/.local/bin:${PATH}"

EXPOSE 5000

# Compose replaces this command with the development server.
CMD ["sh", "-c", "python src/migrate.py && exec gunicorn --chdir src --bind 0.0.0.0:5000 --access-logfile - app:app"]
