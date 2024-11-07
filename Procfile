web: gunicorn conf.wsgi
worker: celery -A promo worker -B --loglevel=info
beat: celery -A promo beat --loglevel=info

