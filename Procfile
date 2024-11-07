web: gunicorn conf.wsgi
worker: celery -A conf worker --loglevel=info & celery -A conf beat --loglevel=info


