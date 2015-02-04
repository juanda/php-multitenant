FROM ubuntu:14.04
MAINTAINER Juanda

RUN apt-get update && apt-get -y install apache2 && apt-get clean

ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_LOG_DIR /var/log/apache2

RUN a2enmod proxy_fcgi

ADD VirtualHost /etc/apache2/sites-available/000-default.conf
ADD envvars /etc/apache2/envvars

EXPOSE 80

CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
