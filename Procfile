web: gunicorn conf.wsgi
worker: celery -A your_app worker --loglevel=info
beat: celery -A your_app beat --loglevel=info

