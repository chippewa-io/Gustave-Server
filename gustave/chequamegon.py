import requests
import time
import os
import signal
import sys

# import config
sys.path.append('/etc/gustave')
from config import ProductionConfig as Config


SERVER = "https://chequamegon.chippewa.io"
def run_activation_check():
    while True:
        time.sleep(5)
        license_key = Config.ACTIVATION_CODE
        print("Starting activation check...")
        print(f"Verifying license with Server: {SERVER}")
        print(f"License key: {Config.ACTIVATION_CODE}")
        data = {"license_key": license_key}
        try:
            response = requests.post(f"{SERVER}/api/verify", json=data, timeout=60)  # Add timeout to handle potential hangs
            
            # If server returns a non-200 and non-404 status code
            if response.status_code not in [200, 404]:
                print(f"Unexpected status code {response.status_code}")
                time.sleep(7 * 24 * 60 * 60)
                continue
            
            # If server returns a 200 OK status
            if response.status_code == 200:
                result = response.json()
                print (result)
                
                # Only halt the program when License is suspended
                if result.get('message') == 'License suspended':  
                    os.kill(os.getpid(), signal.SIGINT)
                    
            # If server returns a 404, handle it gracefully
            elif response.status_code == 404:
                print("Received 404: License might not be found or there's an issue with the server")

        except requests.RequestException as e:
            print(f"Error contacting activation server: {e}")

        # Sleep for a time before checking again
        time.sleep(600)