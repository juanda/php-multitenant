FROM ubuntu:14.04
MAINTAINER Juanda

RUN apt-get update && \
    apt-get -y dist-upgrade

RUN apt-get -y install php5 php5-fpm php5-gd \
    php5-sqlite php5-mysqlnd \
    php5-mcrypt php5-xmlrpc php5-curl

RUN sed -i '/daemonize /c \
daemonize = no' /etc/php5/fpm/php-fpm.conf

RUN sed -i '/^listen /c \
listen = 0.0.0.0:9000' /etc/php5/fpm/pool.d/www.conf

RUN sed -i 's/^listen.allowed_clients/;listen.allowed_clients/' /etc/php5/fpm/pool.d/www.conf

RUN mkdir /moodledata
RUN chown -R www-data:www-data /moodledata

EXPOSE 9000
ENTRYPOINT ["php5-fpm"]
