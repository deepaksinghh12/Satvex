FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app
RUN chmod +x /app/docker-entrypoint.sh || true
RUN adduser --disabled-password --gecos "" appuser || true
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Use an entrypoint script to run migrations and start Gunicorn
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]