web: gunicorn wsgi:app --timeout 0
worker: celery -A AlgoLaw_Website.AlgoLawWeb.celery worker --pool=solo --loglevel=info
