import subprocess
import re
import time
import requests

def concierge():
    regex = r'^[a-fA-F0-9]{32}$'
    secret = subprocess.getoutput("defaults read /Library/Managed\ Preferences/io.chippewa.gustave.plist Secret")
    
    if re.match(regex, secret):
        print("Secret already exists.")
        return

    UDID = subprocess.getoutput("system_profiler SPHardwareDataType | awk '/UUID/ { print $3;}'")
    GustaveServer = "gustave.chippewa.io"
    response = requests.post(f"https://{GustaveServer}/api/secret", data={'udid': UDID})

    max_attempts = 30
    attempt = 0
    while True:
        secret = subprocess.getoutput("defaults read /Library/Managed\ Preferences/io.chippewa.gustave.plist Secret")
        if re.match(regex, secret):
            print("Secret received.")
            break
        elif attempt == max_attempts:
            print("Maximum attempts reached. Exiting.")
            return
        else:
            attempt += 1
        time.sleep(1)

# Calling the function
concierge()
