web: gunicorn wsgi:app --timeout 0
worker: celery -A worker --app=AlgoLaw_Website.AlgoLawWeb.celery --pool=solo--loglevel=info
