#!/usr/bin/env bash

sudo docker build -t juandalibaba/apache DockerfileApache
sudo docker build -t juandalibaba/php-fpm DockerfilePhpFpm
sudo docker pull jwilder/nginx-proxy