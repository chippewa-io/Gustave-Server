import requests
import time
import os
import sys
import logging

###############################################
# Add the path to the custom config file
sys.path.append('/etc/gustave')

###############################################
# Load config
from gustave_config import ProductionConfig as Config

###############################################
# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

###############################################
# License Server Variables
SERVER = "https://chequamegon.chippewa.io"
CHECK_INTERVAL = 600  # 10 minutes
SLEEP_ON_ERROR = 7 * 24 * 60 * 60  # 7 days

###############################################
# RUN
def run_activation_check():
    while True:
        license_key = Config.ACTIVATION_CODE
        logging.info("Starting activation check...")
        logging.info(f"Verifying license with Server: {SERVER}")
        logging.info(f"License key: {Config.ACTIVATION_CODE}")
        data = {"license_key": license_key}

        try:
            response = requests.post(f"{SERVER}/api/verify", json=data, timeout=60)  # Add timeout to handle potential hangs
            
            if response.status_code not in [200, 404]:
                logging.error(f"Unexpected status code {response.status_code}")
                time.sleep(SLEEP_ON_ERROR)
                continue
            
            if response.status_code == 200:
                result = response.json()
                logging.info(result)
                
                if result.get('message') == 'License suspended':
                    os.kill(os.getpid(), signal.SIGINT)
                    
            elif response.status_code == 404:
                logging.warning("Received 404: License might not be found or there's an issue with the server")

        except requests.RequestException as e:
            logging.error(f"Error contacting activation server: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    run_activation_check()