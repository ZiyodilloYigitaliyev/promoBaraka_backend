web: gunicorn conf.wsgi
worker: celery -A task worker --loglevel=info
beat: celery -A task beat --loglevel=info


