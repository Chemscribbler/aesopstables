web: flask db upgrade; gunicorn aesopstables:app
worker: celery --app aesopstables.celery worker --concurrency 4 --beat --loglevel=info
