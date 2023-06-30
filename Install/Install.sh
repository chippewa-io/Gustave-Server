#!/bin/bash
# Check if the script is running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root."
    exit 1
fi

# Check if the script is running on Ubuntu 22.04
if ! grep -q 'Ubuntu 22.04' /etc/os-release; then
    echo "Gustave is only supported on Ubuntu 22.04."
    exit 1
fi

# Check if dialog is installed and install it if not
if ! command -v dialog >/dev/null 2>&1; then
    echo -n "Installer initializing..."
    # Try to install dialog
    apt-get install -y dialog &> /dev/null &
    pid=$! # Process Id of the previous running command

    spin='-\|/'

    i=0
    while kill -0 $pid 2>/dev/null
    do
      i=$(( (i+1) %4 ))
      printf "\b${spin:$i:1}"
      sleep .1
    done
    echo -e "\b done."
fi

# Check again if dialog is installed
if ! command -v dialog >/dev/null 2>&1; then
    echo "Dialog is not installed. Please install it and run the script again."
    exit 1
fi

dialog --title "Welcome" --msgbox "Greetings, esteemed guest! Welcome to the illustrious Gustave installation process. Shall we begin?" 10 40

# Prompt the user for the new values
jamf_pro_url=$(dialog --stdout --inputbox "Dear esteemed guest, may we kindly request the URL of your Jamf Pro server?" 10 60)
jamf_pro_username=$(dialog --stdout --inputbox "Splendid! Now, could you please provide us with your Jamf Pro username?" 10 60)
jamf_pro_password=$(dialog --stdout --passwordbox "Thank you! For security reasons, could you please silently enter your Jamf Pro password?" 10 60)
mysql_host=$(dialog --stdout --inputbox "MySQL Host:" 0 0)
mysql_user=$(dialog --stdout --inputbox "MySQL User:" 0 0)
mysql_password=$(dialog --stdout --passwordbox "MySQL Password:" 0 0)
mysql_db=$(dialog --stdout --inputbox "MySQL Database:" 0 0)
dialog --msgbox "You need to create a special category for Gustave. This will help to keep your Configuration Profiles area of the JSS clean and tidy. We need to know the ID and name of this group." 0 0
category_id=$(dialog --stdout --inputbox "CATEGORY_ID:" 0 0)
category_name=$(dialog --stdout --inputbox "CATEGORY_NAME:" 0 0)

# Output the values into config.py
cat << EOF > config.py
class Config:
    """Base configuration."""
    MYSQL_DATABASE_HOST = '$mysql_host'
    MYSQL_DATABASE_USER = '$mysql_user'
    MYSQL_DATABASE_PASSWORD = '$mysql_password'
    MYSQL_DATABASE_DB = '$mysql_db'
    MYSQL_DATABASE_PORT = 3306
    JAMF_PRO_URL = '$jamf_pro_url'
    JAMF_PRO_USERNAME = '$jamf_pro_username'
    JAMF_PRO_PASSWORD = '$jamf_pro_password'
    CATEGORY_ID = $category_id
    CATEGORY_NAME = "$category_name"
    PROFILE_DESCRIPTION = "This profile is used on the backend of your system.  Please ignore this."

class DevelopmentConfig(Config):
    USE_WAITRESS = False
    DEBUG = True
    TESTING = True
    TOKEN_EXPIRATION = 5 #in seconds.  31556926=year 2629743=month 86400=day 3600=hour

class TestingConfig(Config):
    USE_WAITRESS = False
    TESTING = True
    TOKEN_EXPIRATION = 2629743 #in seconds.  31556926=year 2629743=month 86400=day 3600=hour

class ProductionConfig(Config):
    USE_WAITRESS = True
    TOKEN_EXPIRATION = 2629743 #in seconds.  31556926=year 2629743=month 86400=day 3600=hour
EOF
