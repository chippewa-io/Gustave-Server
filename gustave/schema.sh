#!/bin/bash

###############################################
# Extract MySQL database details from the configuration file
mysql_db=$(grep "MYSQL_DATABASE_DB" /etc/gustave/gustave_config.py | awk -F"'" '{print $2}')
mysql_user=$(grep "MYSQL_DATABASE_USER" /etc/gustave/gustave_config.py | awk -F"'" '{print $2}')
mysql_password=$(grep "MYSQL_DATABASE_PASSWORD" /etc/gustave/gustave_config.py | awk -F"'" '{print $2}')

###############################################
# Create MySQL database and user, and grant privileges
sudo mysql -u root -e "CREATE DATABASE IF NOT EXISTS $mysql_db;"
sudo mysql -u root -e "CREATE USER IF NOT EXISTS '$mysql_user'@'localhost' IDENTIFIED BY '$mysql_password';"
sudo mysql -u root -e "GRANT ALL PRIVILEGES ON $mysql_db.* TO '$mysql_user'@'localhost';"
sudo mysql -u root -e "FLUSH PRIVILEGES;"

###############################################
# Create tables with updated schema
###############################################
# secret_table with detailed schema
sudo mysql -u root -e "USE $mysql_db; CREATE TABLE IF NOT EXISTS secret_table (
  id INT NOT NULL AUTO_INCREMENT,
  udid VARCHAR(255) NOT NULL,
  secret VARCHAR(255) NOT NULL,
  computer_id INT NOT NULL,
  expiration INT NOT NULL,
  is_active TINYINT(1) DEFAULT '1',
  PRIMARY KEY (id)
) ENGINE=InnoDB AUTO_INCREMENT=103 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"

###############################################
# active_profiles with detailed schema
sudo mysql -u root -e "USE $mysql_db; CREATE TABLE IF NOT EXISTS active_profiles (
  profile_id INT NOT NULL,
  computer_id INT NOT NULL,
  PRIMARY KEY (profile_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"

###############################################
# expired_profiles with detailed schema
sudo mysql -u root -e "USE $mysql_db; CREATE TABLE IF NOT EXISTS expired_profiles (
  profile_id INT NOT NULL,
  computer_id INT NOT NULL,
  deletion BIGINT DEFAULT (unix_timestamp() + 60),
  PRIMARY KEY (profile_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"