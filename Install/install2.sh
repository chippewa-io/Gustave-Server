#!/bin/bash
###############################################################################
#                                   Variables                                 #
###############################################################################
progress_file="/tmp/install_progress.txt"
###############################################################################
# Functions
###############################################################################
check_mysql_installed() {
  if command -v mysql > /dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> install.log
}
###############################################################################
# Check if the script is running as root
###############################################################################
if [ "$(id -u)" -ne 0 ]; then
    log "Please run as root."
    exit 1
fi
###############################################################################
# Check if the script is running on Ubuntu 22.04
###############################################################################
if ! grep -q 'Ubuntu 22.04' /etc/os-release; then
    log "Gustave is only supported on Ubuntu 22.04."
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
###############################################################################
# Check if dialog is installed and install it if not
###############################################################################
if ! command -v dialog >/dev/null 2>&1; then
    log "dialog not installed.  Installing dialog"
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
    log "dialog has been installed"
    echo -e "\b done."
fi
###############################################################################
# Check if python3-apt is installed and install it if not
###############################################################################
if ! command -v python3-apt >/dev/null 2>&1; then
    log "python3-apt not installed.  Installing python3-apt"
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
    log "python3-apt has been installed"
    echo -e "\b done."
fi
###############################################################################
# Start Dialog
###############################################################################
log "starting Dialog now"
dialog --title "Welcome" --msgbox "Greetings, esteemed guest! Welcome to the illustrious Gustave installation process. Shall we begin?" 10 40
###############################################################################
if check_mysql_installed; then
  log "MySQL is already installed."
else
  log "MySQL is not installed."
  # Ask the user if they want to install MySQL
  if dialog --yesno "MySQL is not installed. Do you want to install it?" 10 40; then
    # User chose to install MySQL
    echo -n "Installer initializing..."
    # Try to install MySQL
    sudo python3 ./progress.py > /dev/null 2>&1 &
    if [ $? -eq 0 ]; then
      log "MySQL has been installed"
    else
      log "Failed to install MySQL"
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
      log "MySQL was installed successfully."
      install_mysql=1
    else
      log "MySQL was not installed successfully."
      dialog --title "Installation Error" --msgbox "MySQL was not installed successfully. Please check the log for more information." 10 40
      exit 1
    fi
  else
    # User chose not to install MySQL
    log "User chose not to install MySQL."
    install_mysql=0
  fi
fi

#//////////////////////////////////////////////////////////////////////////////
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@    MySQL          @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
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
  log "Creating the database."
  dialog --infobox "Creating the database..." 10 40
  # Create the database
  sudo mysql -h "$mysql_host" -u root -e "CREATE DATABASE secrets;"
  sudo mysql -h "$mysql_host" -u root -e "CREATE DATABASE secrets;"
  sudo mysql -h "$mysql_host" -u root -e "CREATE DATABASE secrets;"
  # Check if the database was created successfully
  if [ $? -eq 0 ]; then
    log "Database created successfully."
  else
    log "Failed to create database."
    dialog --title "Database Error" --msgbox "Failed to create database. Please check the log for more information." 10 40
    exit 1
  fi
fi
#//////////////////////////////////////////////////////////////////////////////#
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@    Jamf Pro          @@@@@@@@@@@@@@@@@@@@@@@@@@@@#
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
token=$(curl -s -X GET "$jamf_pro_url/api/v1/auth" -u "$jamf_pro_username:$jamf_pro_password" | jq -r '.token')
# Create the category and get the ID
response=$(curl -s -X POST "$jamf_pro_url/api/v1/categories" -H "accept: application/json" -H "Content-Type: application/json" -H "Authorization: Bearer $token" -d "{\"name\":\"$category_name\",\"priority\":9}")
category_id=$(echo "$response" | jq -r '.id')
# Check if the category was created successfully
if [[ "$category_id" == null ]]; then
  dialog --title "API Error" --msgbox "Bro, there was an error creating the category. Check your Jamf Pro URL and credentials and try again." 10 40
  exit 1
fi

