#!/bin/bash


#//////////////////////////////////////////////////////////////////////////////
#||||||||||||||||||||||||||    Setup          |||||||||||||||||||||||||||||||||
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

###############################################################################
#                                  Variables                                  #
###############################################################################

progress_file="/tmp/install_progress.txt"

###############################################################################
#                                   Functions                                 #
###############################################################################

check_mysql_installed() {
  if command -v mysql > /dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

log() {
    local level="$2"
    local message="$1"
    local lineno="${BASH_LINENO[0]}"
    if [ "$level" = "ERROR" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $level:$lineno - $message" >> install.log
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $level - $message" >> install.log
    fi
}

###############################################################################
#                  Check if the script is running as root                     #
###############################################################################

if [ "$(id -u)" -ne 0 ]; then
    log "Please run as root." "ERROR"
    exit 1
fi

###############################################################################
#               Check if the script is running on Ubuntu 22.04                #
###############################################################################

if ! grep -q 'Ubuntu 22.04' /etc/os-release; then
    log "Gustave is only supported on Ubuntu 22.04." "ERROR"
    exit 1
fi

###############################################################################
#Updating package index
###############################################################################

echo -n "Updating package index..."
sudo apt update &> /dev/null &
pid=$! # Process Id of the previous running command

spin='-\|/'

i=0
while kill -0 $pid 2>/dev/null
do
  i=$(( (i+1) %4 ))
  printf "\b${spin:$i:1}"
  sleep .1
done
wait $pid
echo -e "\b done."


#//////////////////////////////////////////////////////////////////////////////
#|||||||||||||||||||       Install Dependencies          ||||||||||||||||||||||
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

###############################################################################
#               Check if jq is installed and install it if not                #
###############################################################################

if ! command -v jq >/dev/null 2>&1; then
    log "jq not installed.  Installing jq" "INFO"
    # Try to install jq
    sudo apt install -y jq &> /dev/null &
    pid=$! # Process Id of the previous running command

    spin='-\|/'

    i=0
    while kill -0 $pid 2>/dev/null
    do
      i=$(( (i+1) %4 ))
      printf "\b${spin:$i:1}"
      sleep .1
    done
    wait $pid
    log "jq has been installed" "INFO"
    echo -e "\b done."
fi

###############################################################################
#               Check if dialog is installed and install it if not            #
###############################################################################

if ! command -v dialog >/dev/null 2>&1; then
    log "dialog not installed.  Installing dialog" "INFO"
    echo -n "Installing dependencies..."
    # Try to install dialog
    sudo apt install -y dialog &> /dev/null &
    pid=$! # Process Id of the previous running command

    spin='-\|/'

    i=0
    while kill -0 $pid 2>/dev/null
    do
      i=$(( (i+1) %4 ))
      printf "\b${spin:$i:1}"
      sleep .1
    done
    wait $pid
    log "dialog has been installed" "INFO"
    echo -e "\b done."
fi

###############################################################################
#          Check if python3-apt is installed and install it if not            #
###############################################################################

if ! command -v python3-apt >/dev/null 2>&1; then
    log "python3-apt not installed.  Installing python3-apt" "INFO"
    echo -n "Installing dependencies..."
    # Try to install python3-apt
    sudo apt install -y python3-apt &> /dev/null &
    pid=$! # Process Id of the previous running command

    spin='-\|/'

    i=0
    while kill -0 $pid 2>/dev/null
    do
      i=$(( (i+1) %4 ))
      printf "\b${spin:$i:1}"
      sleep .1
    done
    wait $pid
    log "python3-apt has been installed" "INFO"
    echo -e "\b done."
fi


#//////////////////////////////////////////////////////////////////////////////
#/////////////////////////           Begin          ///////////////////////////
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

###############################################################################
#                                  Start Dialog                               #
###############################################################################

log "starting Dialog now" "INFO"
dialog --title "Welcome" --msgbox "Greetings, esteemed guest! Welcome to the illustrious Gustave installation process. Shall we begin?" 10 40


#//////////////////////////////////////////////////////////////////////////////#
#|||||||||||||||||||||||||       Activation        |||||||||||||||||||||||||||||#
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#

license=$(dialog --stdout --inputbox "Splendid! Now, could you please provide us with your Activation Code?" 10 60)


###############################################################################
if check_mysql_installed; then
  log "MySQL is already installed." "INFO"
else
  log "MySQL is not installed." "INFO"
  # Ask the user if they want to install MySQL
  if dialog --yesno "MySQL is not installed. Do you want to install it?" 10 40; then
    # User chose to install MySQL
    echo -n "Installer initializing..."
    # Try to install MySQL
    sudo python3 ./progress.py > /dev/null 2>&1 &
    if [ $? -eq 0 ]; then
      log "MySQL has been installed" "INFO"
    else
      log "Failed to install MySQL" "ERROR"
    fi
    echo -e "\\b done."

    while [ ! -f $progress_file ]
    do
      sleep 0.1
    done

    (
    while true
    do
        # Get the last line of the progress file that contains 'Percent' and extract the percentage
        progress=$(grep 'Percent:' $progress_file | tail -n1 | awk -F 'Percent: ' '{ print $2 }' | awk -F '.' '{ print $1 }')

        # Check if the progress is 100, if so, break the loop
        if [ "$progress" == "100" ]; then
            break
        fi

        # Update the dialog command's progress bar
        echo $progress

        # Wait a bit before checking the progress again
        sleep 0.1
    done
    ) | dialog --gauge "Installing MySQL..." 10 70 0
    # Check if MySQL was installed successfully
    if check_mysql_installed; then
      log "MySQL was installed successfully." "INFO"
      install_mysql=1
    else
      log "MySQL was not installed successfully." "ERROR"
      dialog --title "Installation Error" --msgbox "MySQL was not installed successfully. Please check the log for more information." 10 40
      exit 1
    fi
  else
    # User chose not to install MySQL
    log "User chose not to install MySQL." "INFO"
    install_mysql=0
  fi
fi


#//////////////////////////////////////////////////////////////////////////////
#||||||||||||||||||||||||||||    MySQL          ||||||||||||||||||||||||||||||
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

###############################################################################
# Prompt the user for MySQL Values
###############################################################################
mysql_host=$(dialog --stdout --inputbox "MySQL Host:" 0 0)
mysql_user=$(dialog --stdout --inputbox "MySQL User:" 0 0)
mysql_password=$(dialog --stdout --passwordbox "MySQL Password:" 0 0)
mysql_db=$(dialog --stdout --inputbox "MySQL Database:" 0 0)
###############################################################################
# Create the database                                                         #
###############################################################################
if [ "$install_mysql" != "0" ]; then
  log "Creating the database." "INFO"
  dialog --infobox "Creating the database..." 10 40
  # Create the database
  sudo mysql -u root -e "CREATE DATABASE $mysql_db;"
  sudo mysql -u root -e "CREATE USER '$mysql_user'@'localhost' IDENTIFIED BY '$mysql_password';"
  sudo mysql -u root -e "GRANT ALL PRIVILEGES ON $mysql_db.* TO '$mysql_user'@'localhost';"
  sudo mysql -u root -e "FLUSH PRIVILEGES;"
  sudo mysql -u root -e "USE $mysql_db; CREATE TABLE secret_table (udid VARCHAR(255) NOT NULL, secret VARCHAR(255) NOT NULL, computer_id INT NOT NULL, expiration INT NOT NULL, PRIMARY KEY (udid));"
  sudo mysql -u root -e "USE $mysql_db; CREATE TABLE active_profiles (profile_id INT NOT NULL, computer_id INT NOT NULL, PRIMARY KEY (profile_id));"
  sudo mysql -u root -e "USE $mysql_db; CREATE TABLE expired_profiles (profile_id INT NOT NULL, computer_id INT NOT NULL, PRIMARY KEY (profile_id));"

  # Check if the database was created successfully
  if [ $? -eq 0 ]; then
    log "Database created successfully." "INFO"
  else
    log "Failed to create database." "ERROR"
    dialog --title "Database Error" --msgbox "Failed to create database. Please check the log for more information." 10 40
    exit 1
  fi
fi


#//////////////////////////////////////////////////////////////////////////////#
#|||||||||||||||||||||||||       Jamf Pro        |||||||||||||||||||||||||||||#
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#

jamf_pro_url=""
while [[ ! $jamf_pro_url =~ ^https:// ]]; do
  jamf_pro_url=$(dialog --stdout --inputbox "Dear esteemed guest, may we kindly request the URL of your Jamf Pro server?" 10 60)
  if [[ -z "$jamf_pro_url" ]]; then
    dialog --title "Input Required" --msgbox "Bro, you gotta give me the URL of your Jamf Pro server. It's required!" 10 40
  elif [[ ! $jamf_pro_url =~ ^https:// ]]; then
    dialog --title "Invalid Input" --msgbox "Bro, the URL of your Jamf Pro server should start with 'https://'. Let's try that again!" 10 40
    jamf_pro_url="" # Reset the variable to prompt the user again
  fi
done

jamf_pro_username=""
while [[ -z "$jamf_pro_username" ]]; do
  jamf_pro_username=$(dialog --stdout --inputbox "Splendid! Now, could you please provide us with your Jamf Pro username?" 10 60)
  if [[ -z "$jamf_pro_username" ]]; then
    dialog --title "Input Required" --msgbox "Bro, you gotta give me your Jamf Pro username. It's required!" 10 40
  fi
done

jamf_pro_password=""
while [[ -z "$jamf_pro_password" ]]; do
  jamf_pro_password=$(dialog --stdout --passwordbox "Thank you! For security reasons, could you please silently enter your Jamf Pro password?" 10 60)
  if [[ -z "$jamf_pro_password" ]]; then
    dialog --title "Input Required" --msgbox "Bro, you gotta give me your Jamf Pro password. It's required!" 10 40
  elif [[ "$jamf_pro_password" == "jamf1234" ]]; then
    dialog --title "Weak Password Alert" --msgbox "Bro, 'jamf1234'? You should really change your password. But for now, let's continue." 10 40
  fi
done
category_name=""
while [[ -z "$category_name" ]]; do
  category_name=$(dialog --stdout --inputbox "CATEGORY_NAME:" 0 0)
  if [[ -z "$category_name" ]]; then
    dialog --title "Input Required" --msgbox "Bro, you gotta give me the category name. It's required!" 10 40
  fi
done
###############################################################################
# Create the category in Jamf Pro
###############################################################################
requestToken=$(curl -s -u "$jamf_pro_username":"$jamf_pro_password" "$jamf_pro_url"/api/v1/auth/token -X POST)
token=$(echo "$requestToken" | jq -r '.token')
# Create the category and get the ID
response=$(curl -s -X POST "$jamf_pro_url/api/v1/categories" -H "accept: application/json" -H "Content-Type: application/json" -H "Authorization: Bearer $token" -d "{\"name\":\"$category_name\",\"priority\":9}")
category_id=$(echo "$response" | jq -r '.id')
# Check if the category was created successfully
if [[ "$category_id" == null ]]; then
  dialog --title "API Error" --msgbox "Bro, there was an error creating the category. Check your Jamf Pro URL and credentials and try again." 10 40
  log "Failed to create category." "ERROR"
  exit 1
fi


#//////////////////////////////////////////////////////////////////////////////#
#@@@@@@@@@@@@@@@@@@@    Creat the config.py        @@@@@@@@@@@@@@@@@@@@@@@@@@@@#
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#

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
log "config.py generated" "INFO"


#//////////////////////////////////////////////////////////////////////////////#
#|||||||||||    Create the service and directory structure      |||||||||||||||#
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#

###############################################################################
# Create the gustave user
###############################################################################
dialog --infobox "Creating gustave user..." 10 40
log "Creating gustave user." "INFO"
sleep 1
sudo adduser --system --group gustave
if [ $? -eq 0 ]; then
    log "Created the gustave user." "INFO"
else
    log "Failed to create the gustave user." "ERROR"
fi

###############################################################################
#Create directory
###############################################################################
dialog --infobox "Creating gustave directory..." 10 40
sudo mkdir -p /etc/gustave
if [ $? -eq 0 ]; then
    log "Created the gustave directory." "INFO"
else
    log "Failed to create the gustave directory." "ERROR"
fi

###############################################################################
# Move the gustave executable to the proper location
###############################################################################
dialog --infobox "Moving the gustave executable to the proper location..." 10 40
sleep 1
sudo mv ./gustave /usr/local/bin/gustave
if [ $? -eq 0 ]; then
    log "gustave moved properly." "INFO"
else
    log "Failed to move gustave." "ERROR"
fi

###############################################################################
# Set the owner to gustave
###############################################################################
dialog --infobox "Setting the owner to gustave..." 10 40
sleep 1
sudo chown gustave:gustave /usr/local/bin/gustave
if [ $? -eq 0 ]; then
    log "permissions configured for gustave." "INFO"
else
    log "Failed to configure for gustave." "ERROR"
fi

###############################################################################
# Set the permissions
###############################################################################
dialog --infobox "Setting the permissions..." 10 40
sleep 1
sudo chmod 755 /usr/local/bin/gustave
if [ $? -eq 0 ]; then
    log "modified gustave." "INFO"
else
    log "Failed to modify gustave." "ERROR"
fi

###############################################################################
# Move the gustave.service file to the systemd directory
###############################################################################
dialog --infobox "Moving the Gustave service file to the systemd directory..." 10 40
sleep 1
sudo mv ./gustave.service /etc/systemd/system/gustave.service
if [ $? -eq 0 ]; then
    log "Created gustave service." "INFO"
else
    log "Failed to create gustave service." "ERROR"
fi

###############################################################################
# Set the owner and permissions for the service file
###############################################################################
dialog --infobox "Setting the owner and permissions for the service file..." 10 40
sleep 1
sudo chown root:root /etc/systemd/system/gustave.service
if [ $? -eq 0 ]; then
    log "Set owner /etc/systemd/system/gustave.service to root:root." "INFO"
else
    log "Failed to Set owner /etc/systemd/system/gustave.service to root:root." "ERROR"
fi
sleep 1
sudo chmod 644 /etc/systemd/system/gustave.service
if [ $? -eq 0 ]; then
    log "modified /etc/systemd/system/gustave.service to 644." "INFO"
else
    log "Failed to modify /etc/systemd/system/gustave.service to 644." "ERROR"
fi

###############################################################################
# Move the config.py file to the proper location
###############################################################################
dialog --infobox "Moving the config.py file to the proper location..." 10 40
sleep 1
sudo mv ./config.py /etc/gustave/config.py
if [ $? -eq 0 ]; then
    log "Moved config.py into place." "INFO"
else
    log "Failed to move config.py into place" "ERROR"
fi

###############################################################################
# Set the owner and permissions for the config file
###############################################################################
dialog --infobox "Setting the owner and permissions for the config file..." 10 40
sleep 1
sudo chown gustave:gustave /etc/gustave/config.py
if [ $? -eq 0 ]; then
    log "Set owner /etc/gustave/config.py to gustave:gustave." "INFO"
else
    log "Failed to set owner /etc/gustave/config.py to gustave:gustave." "ERROR"
fi
sleep 1
sudo chmod 644 /etc/gustave/config.py
if [ $? -eq 0 ]; then
    log "modified /etc/gustave/config.py to 644." "INFO"
else
    log "Failed to modify /etc/gustave/config.py to 644." "ERROR"
fi
sleep 1

###############################################################################
# Reload the systemd daemon to recognize the new service
###############################################################################
dialog --infobox "Reloading the systemd daemon to recognize the new service..." 10 40
sudo systemctl daemon-reload
if [ $? -eq 0 ]; then
    log "Reloaded the systemd daemon." "INFO"
else
    log "Failed to reload the systemd daemon." "ERROR"
fi
sleep 1

###############################################################################
# Enable the service so it starts on boot
###############################################################################
dialog --infobox "Enabling the service so it starts on boot..." 10 40
sudo systemctl enable gustave
if [ $? -eq 0 ]; then
    log "Enabled the gustave service." "INFO"
else
    log "Failed to enable the gustave service." "ERROR"
fi
sleep 1

###############################################################################
# Start the service
###############################################################################
dialog --infobox "Starting the service..." 10 40
sudo systemctl start gustave
if [ $? -eq 0 ]; then
    log "Started the gustave service." "INFO"
else
    log "Failed to start the gustave service." "ERROR"
fi
sleep 1

# Check if service is running
systemctl is-active --quiet gustave
if [ $? -eq 0 ]; then
    activate=1
    log "gustave service is running." "INFO"
else
    activate=0
    log "gustave service is not running." "ERROR"
fi

if [ $activate -eq 1 ]; then
    dialog --msgbox "Installation complete!  Activating product..." 0 0
    log "Reaching out to activate license" "INFO"
    response=$(curl -s -X POST -H "Content-Type: application/json" -d "{\"license_key\":\"$license\"}" https://chequamegon.chippewa.io/api/activate)
    status=$(echo $response | jq -r '.message')
    if [ "$status" == "License activated" ]; then
        dialog --msgbox "Activation successful!" 0 0
        expiry=$(curl -s -X POST -H "Content-Type: application/json" -d "{\"license_key\":\"$license\"}" $server/api/verify | jq -r '.remaining_time')
        log "Checked in" "INFO"
    else
        dialog --msgbox "Activation failed!  Please examine the log to ensure there were no errors." 0 0
        log "Activation failed!" "ERROR"
        clear
        exit 1
    fi
    clear
    exit 0
else
    dialog --msgbox "Installation failed!  Please examine the log to ensure there were no errors." 0 0
    log "Installation failed!" "ERROR"
    clear
    exit 1
fi


#//////////////////////////////////////////////////////////////////////////////#
#|||||||||||||||||||||||||       Finish Up        |||||||||||||||||||||||||||||#
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#

###############################################################################
# Completion message
###############################################################################
dialog --msgbox "Installation complete!  Please examine the log to ensure there were no errors." 0 0
log "Installation complete!" "INFO"
clear
exit 0
###############################################################################