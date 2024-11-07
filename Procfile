web: gunicorn conf.wsgi
worker: celery -A promo worker --loglevel=info
beat: celery -A promo beat --loglevel=info


