FROM httpd:2.4

# Enable mod_proxy and mod_proxy_http (commented out by default in the official image)
RUN sed -i \
    -e 's/#LoadModule proxy_module/LoadModule proxy_module/' \
    -e 's/#LoadModule proxy_http_module/LoadModule proxy_http_module/' \
    /usr/local/apache2/conf/httpd.conf

COPY corail.conf /usr/local/apache2/conf/extra/corail.conf
RUN echo "Include conf/extra/corail.conf" >> /usr/local/apache2/conf/httpd.conf
