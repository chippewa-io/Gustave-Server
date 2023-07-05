#!/bin/bash

#check if being run by sudo
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

#Remove MySQL
sudo apt -y autoremove mysql-server mysql-client mysql-common
sudo apt -y purge mysql-server mysql-client mysql-common
sudo rm -rf /etc/mysql /var/lib/mysql
sudo rm -rf /usr/bin/mysql