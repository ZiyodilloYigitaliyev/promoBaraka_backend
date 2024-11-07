web: gunicorn conf.wsgi
worker: celery -A promo worker --loglevel=info & celery -A promo beat --loglevel=info


