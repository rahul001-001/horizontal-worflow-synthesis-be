web: gunicorn backend.wsgi:application --bind 0.0.0.0:8000
worker: celery -A backend worker -l info