web: flask db upgrade; gunicorn aesopstables:app
worker: celery worker --app=aesopstables.app --beat --loglevel=info