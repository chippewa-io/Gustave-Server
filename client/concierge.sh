#!/bin/zsh


function concierge {

  regex='^[a-fA-F0-9]{32}$'
  secret=$(defaults read /Library/Managed\ Preferences/io.chippewa.gustave.plist Secret 2>/dev/null)
  
  if [[ $secret =~ $regex ]]; then
    echo "Secret already exists."
    check_secret_status "$secret"
    return 0
  fi

  UDID=$(system_profiler SPHardwareDataType | awk '/UUID/ { print $3;}')
  GustaveServer=$(defaults read /Library/Managed\ Preferences/io.chippewa.gustave.plist GustaveServerURL 2>/dev/null)

  attempts=0
  max_attempts=$(defaults read /Library/Managed\ Preferences/io.chippewa.gustave.plist Timeout 2>/dev/null)
  new_secret=""
  curl -X POST -F "udid"="$UDID" https://$GustaveServer/api/secret
  while [[ ! $new_secret =~ $regex && $attempts -lt $max_attempts ]]; do
    ((attempts++))
    sleep 2

    
    new_secret=$(defaults read /Library/Managed\ Preferences/io.chippewa.gustave.plist Secret 2>/dev/null)

    if [[ $new_secret =~ $regex ]]; then
      echo "Secret received."
      store_secret_in_database "$new_secret"
      check_secret_status "$new_secret"
    else
      echo "Failed to receive the secret."
      if [[ $attempts -lt $max_attempts ]]; then
        echo "Retrying in 1 second..."
        sleep 1
      else
        echo "Exiting after $max_attempts attempts."
        return 1
      fi
    fi
  done
}

function store_secret_in_database {
  secret=$1
  database="/Library/Application Support/gustave/test.database.db"

  # Create the database table if it doesn't exist
  sqlite3 "$database" "CREATE TABLE IF NOT EXISTS secrets (id INTEGER PRIMARY KEY AUTOINCREMENT, secret TEXT, expiration TEXT);"

  # Get the expiration date from the /api/secret/expiration endpoint
  GustaveServer=$(defaults read /Library/Managed\ Preferences/io.chippewa.gustave.plist GustaveServerURL 2>/dev/null)
  expiration=$(curl -s "https://$GustaveServer/api/secret/expiration?secret=$secret" | jq -r '.expiration_date')

  # Insert the secret and expiration date into the database
  sqlite3 "$database" "INSERT INTO secrets (secret, expiration) VALUES ('$secret', '$expiration');"

  echo "Secret stored in the database."
}

function check_secret_status {
  secret=$1
  GustaveServer=$(defaults read /Library/Managed\ Preferences/io.chippewa.gustave.plist GustaveServerURL 2>/dev/null)
  expiration=$(curl -s "https://$GustaveServer/api/secret/expiration?secret=$secret" | jq -r '.expiration_date')

  if [[ $expiration == "active" ]]; then
    echo "Secret is active."
  else
    echo "Secret is not active or expired."
  fi
}

# The function can then be called with:
concierge