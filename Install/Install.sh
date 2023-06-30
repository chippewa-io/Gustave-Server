#!/bin/bash

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> install.log
}

# Check if the script is running as root
if [ "$(id -u)" -ne 0 ]; then
    log "Please run as root."
    exit 1
fi

# Check if the script is running on Ubuntu 22.04
if ! grep -q 'Ubuntu 22.04' /etc/os-release; then
    log "Gustave is only supported on Ubuntu 22.04."
    exit 1
fi

# Check if dialog is installed and install it if not
if ! command -v dialog >/dev/null 2>&1; then
    log "dialog not installed.  Installing dialog"
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
    log "dialog has been installed"
    echo -e "\b done."
fi

# Check again if dialog is installed
if ! command -v dialog >/dev/null 2>&1; then
    log "Dialog is not installed. Please install it and run the script again."
    exit 1
fi
log "starting Dialog now"
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
log "config.py generated"
# Create the gustave user
dialog --infobox "Creating the Gustave user..." 10 40
sudo adduser --system --group gustave
if [ $? -eq 0 ]; then
    log "Gustave user created successfully."
else
    log "Failed to create Gustave user."
fi

# Move the gustave executable to the proper location
dialog --infobox "Moving the Gustave executable to the proper location..." 10 40
sudo mv /path/to/gustave /usr/local/gustave
if [ $? -eq 0 ]; then
    log "gustave moved properly."
else
    log "Failed to move gustave."
fi

# Set the owner to gustave
dialog --infobox "Setting the owner to Gustave..." 10 40
sudo chown gustave:gustave /proper/location/gustave
if [ $? -eq 0 ]; then
    log "permissions configured for gustave."
else
    log "Failed to configure for gustave."
fi

# Set the permissions
dialog --infobox "Setting the permissions..." 10 40
sudo chmod 755 /proper/location/gustave
if [ $? -eq 0 ]; then
    log "modified gustave."
else
    log "Failed to modify gustave."
fi

# Move the gustave.service file to the systemd directory
dialog --infobox "Moving the Gustave service file to the systemd directory..." 10 40
sudo mv /path/to/gustave.service /etc/systemd/system/gustave.service
if [ $? -eq 0 ]; then
    log "Created gustave service."
else
    log "Failed to create gustave service."
fi

# Set the owner and permissions for the service file
dialog --infobox "Setting the owner and permissions for the service file..." 10 40
sudo chown root:root /etc/systemd/system/gustave.service
if [ $? -eq 0 ]; then
    log "Set owner /etc/systemd/system/gustave.service to root:root."
else
    log "Failed to Set owner /etc/systemd/system/gustave.service to root:root."
fi
sudo chmod 644 /etc/systemd/system/gustave.service
if [ $? -eq 0 ]; then
    log "modified /etc/systemd/system/gustave.service to 644."
else
    log "Failed to modify /etc/systemd/system/gustave.service to 644."
fi

# Move the config.py file to the proper location
dialog --infobox "Moving the config.py file to the proper location..." 10 40
sudo mv /path/to/config.py /proper/location/config.py
if [ $? -eq 0 ]; then
    log "Moved config.py into place."
else
    log "Failed to move config.py into place"
fi

# Set the owner and permissions for the config file
dialog --infobox "Setting the owner and permissions for the config file..." 10 40
sudo chown gustave:gustave /proper/location/config.py

sudo chmod 644 /proper/location/config.py

# Reload the systemd daemon to recognize the new service
dialog --infobox "Reloading the systemd daemon to recognize the new service..." 10 40
sudo systemctl daemon-reload

# Enable the service so it starts on boot
dialog --infobox "Enabling the service so it starts on boot..." 10 40
sudo systemctl enable gustave

# Start the service
dialog --infobox "Starting the service..." 10 40
sudo systemctl start gustave

dialog --msgbox "Installation complete! Gustave is now up and running." 10 40