FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    apache2 \
    libjpeg-dev \
    libpng-dev \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

RUN a2enmod proxy proxy_http

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY docker/apache/corail.conf /etc/apache2/sites-available/corail.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN a2dissite 000-default && a2ensite corail

RUN chmod +x /app/entrypoint.sh

EXPOSE 80

CMD ["/app/entrypoint.sh"]
