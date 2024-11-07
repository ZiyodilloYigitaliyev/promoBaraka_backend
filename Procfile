web: gunicorn conf.wsgi
worker: celery -A task worker --loglevel=info & celery -A task beat --loglevel=info


