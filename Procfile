web: gunicorn conf.wsgi --log-file -
worker: celery -A conf worker --loglevel=info
beat: celery -A conf beat --loglevel=info




