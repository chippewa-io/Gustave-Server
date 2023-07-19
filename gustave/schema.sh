#!/bin/bash

mysql_db=$(cat /etc/gustave/config.py | grep "MYSQL_DATABASE_DB" | awk -F"'" '{print $2}')
mysql_user=$(cat /etc/gustave/config.py | grep "MYSQL_DATABASE_USER" | awk -F"'" '{print $2}')
mysql_password=$(cat /etc/gustave/config.py | grep "MYSQL_DATABASE_PASSWORD" | awk -F"'" '{print $2}')

sudo mysql -u root -e "CREATE DATABASE $mysql_db;"
sudo mysql -u root -e "CREATE USER '$mysql_user'@'localhost' IDENTIFIED BY '$mysql_password';"
sudo mysql -u root -e "GRANT ALL PRIVILEGES ON $mysql_db.* TO '$mysql_user'@'localhost';"
sudo mysql -u root -e "FLUSH PRIVILEGES;"

# Modified the secret_table creation query to include the id and is_active columns
sudo mysql -u root -e "USE $mysql_db; CREATE TABLE secret_table (id INT AUTO_INCREMENT PRIMARY KEY, udid VARCHAR(255) NOT NULL UNIQUE, secret VARCHAR(255) NOT NULL, computer_id INT NOT NULL, expiration INT NOT NULL, is_active BOOLEAN DEFAULT TRUE);"

# The other tables remain unchanged
sudo mysql -u root -e "USE $mysql_db; CREATE TABLE active_profiles (profile_id INT NOT NULL, computer_id INT NOT NULL, PRIMARY KEY (profile_id));"
sudo mysql -u root -e "USE $mysql_db; CREATE TABLE expired_profiles (profile_id INT NOT NULL, computer_id INT NOT NULL, PRIMARY KEY (profile_id));"
