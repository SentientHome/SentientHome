FROM python:3-onbuild

MAINTAINER oliver@ratzesberger.com

RUN apt-get update && apt-get install -y supervisor
RUN mkdir -p /var/log/supervisor

COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 9001 8888
CMD ["/usr/bin/supervisord"]
