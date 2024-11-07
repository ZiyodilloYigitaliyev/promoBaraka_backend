web: gunicorn conf.wsgi
worker: celery -A celery worker --loglevel=info
beat: celery -A celery beat --loglevel=info


