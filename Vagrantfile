# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/trusty64"

  config.vm.network "forwarded_port", guest: 8080, host: 8080

  config.vm.network "private_network", ip: "192.168.33.10"
  
  config.vm.provision "shell",
    inline: "apt-get update; apt-get -y install curl git fabric python-validictory; curl -sSL https://get.docker.com/ubuntu/ | sudo sh"

end
