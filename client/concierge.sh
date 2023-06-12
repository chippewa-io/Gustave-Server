#!/bin/zsh

function concierge {

  regex='^[a-fA-F0-9]{32}$'
  secret=$(defaults read /Library/Managed\ Preferences/io.chippewa.gustave.plist Secret 2>/dev/null)
  
  if [[ $secret =~ $regex ]]; then
    echo "Secret already exists."
    return 0
  fi

  UDID=$(system_profiler SPHardwareDataType | awk '/UUID/ { print $3;}')
  GustaveServer=gustave.chippewa.io
  curl -X POST -F "udid"="$UDID" https://$GustaveServer/api/secret

  max_attempts=30
  attempt=0
  while true; do
    secret=$(defaults read /Library/Managed\ Preferences/io.chippewa.gustave.plist Secret 2>&1)
    if [[ $secret =~ $regex ]]; then
      echo "Secret received."
      break
    elif [[ $attempt -eq $max_attempts ]]; then
      echo "Maximum attempts reached. Exiting."
      return 1
    else
      let "attempt++"
    fi
    sleep 1
  done
}

# The function can then be called with:
concierge
echo $secret