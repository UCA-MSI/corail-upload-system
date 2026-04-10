### Docker stuff

  * Dockerfile : Python 3.12-slim + Gunicorn
  * entrypoint.sh : migrate → collectstatic → start Gunicorn
  * docker-compose.yml : web + apache services + 3 named volumes
  * docker/apache/Dockerfile : httpd:2.4 with mod_proxy enabled
  * docker/apache/corail.conf : serves /static/ and /media/ directly, proxies rest to Gunicorn
  * requirements.txt : Django + DRF + Pillow + Gunicorn
  * .env.example : documents all required env vars
  * .gitignore : adds .env, staticfiles/, db.sqlite3, media/
  * settings.py : SECRET_KEY, DEBUG, ALLOWED_HOSTS, DB_PATH, CSRF_TRUSTED_ORIGINS all read from env

## To run it
  1. Copy the project to the server, then:
   
    `cp .env.example .env`

  2. Edit .env with your real SECRET_KEY, domain, etc.
  3. Build and start
    
    `docker compose up -d --build`