web: gunicorn conf.wsgi
worker: celery -A promo worker -l info
beat: celery -A promo beat -l info
