## cleaner.py
import time
import sys
import mysql.connector
import logging
import requests
###############################################
# Adjust sys.path to find the config module
sys.path.append('/etc/gustave')
from config import ProductionConfig as Config

###############################################
# Set up logging
log_size = 10 * 1024 * 1024  # 10 MB
handler = logging.handlers.RotatingFileHandler('/var/log/gustave.log', maxBytes=log_size, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)  # This retrieves the logger for the current module
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Database and API operations functions
username = Config.JAMF_PRO_USERNAME
password = Config.JAMF_PRO_PASSWORD
JamfURL = Config.JAMF_PRO_URL
host=Config.MYSQL_DATABASE_HOST
user=Config.MYSQL_DATABASE_USER
dbpass=Config.MYSQL_DATABASE_PASSWORD
database=Config.MYSQL_DATABASE_DB,
port=Config.MYSQL_DATABASE_PORT

###############################################
#Database operations
def query_db():    
    # Establish the MySQL connection using credentials from config.py
    connection = mysql.connector.connect(
        host=Config.MYSQL_DATABASE_HOST,
        user=Config.MYSQL_DATABASE_USER,
        dbpass=Config.MYSQL_DATABASE_PASSWORD,
        database=Config.MYSQL_DATABASE_DB,
        port=Config.MYSQL_DATABASE_PORT
    )

    cursor = connection.cursor()
    
    # Get the current timestamp
    current_epoch_timestamp = int(datetime.now().timestamp())


    # Query to fetch profile IDs from the expired_profiles table where the deletion timestamp has passed
    query = f"SELECT profile_id FROM expired_profiles WHERE deletion < {current_epoch_timestamp}"
    cursor.execute(query)
    expired_profile_ids = [row[0] for row in cursor.fetchall()]

    # Close the cursor and the connection
    cursor.close()
    connection.close()

    return expired_profile_ids

def update_deletion(profile_id):    
    # Establish the MySQL connection using credentials from config.py
    connection = mysql.connector.connect(
        host=Config.MYSQL_DATABASE_HOST,
        user=Config.MYSQL_DATABASE_USER,
        dbpass=Config.MYSQL_DATABASE_PASSWORD,
        database=Config.MYSQL_DATABASE_DB,
        port=Config.MYSQL_DATABASE_PORT
    )

    cursor = connection.cursor()

    # update the deletion timestamp to null for the profile ID
    query = f"UPDATE expired_profiles SET deletion = NULL WHERE profile_id = %s"
    cursor.execute(query, (profile_id,)) 
    connection.commit()
    
    if cursor.rowcount == 1:
        print(f"Successfully updated deletion timestamp for profile ID: {profile_id}")
    else:
        print(f"Failed to update deletion timestamp for profile ID: {profile_id}")
        print(f"cursor: {cursor}")
    # Close the cursor and the connection
    cursor.close()
    connection.close()


###############################################
#Jamf API operations
def generate_token():
    # Define the endpoint URL for token generation based on your Jamf Pro API documentation.
    # This is a placeholder and might need to be updated.
    url = JamfURL + "/uapi/auth/tokens"
    auth = (username, password)
    headers = {"Accept": "application/json"}

    # Make the request to generate the token
    response = requests.post(url, auth=auth, headers=headers)

    # Check if the request was successful and return the token
    if response.status_code == 200:
        jamfToken = response.json().get('token')
        return jamfToken
    else:
        logging.error(f"Failed to generate Jamf Pro API token: {response.content}")
        raise Exception(f"Failed to generate Jamf Pro API token: {response.content}")

def delete_profile(token, profile_id):
    url = JamfURL + "/JSSResource/osxconfigurationprofiles/id/" + str(profile_id)
    headers = {
        "Accept": "application/xml",
        "Content-Type": "application/xml",
        "Authorization": f"Bearer {token}"
    }

    response = requests.delete(url, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200 or response.status_code == 404:
        print(f"Successfully processed profile with ID: {profile_id}")
        return True
    else:
        # Parse the response content only if it exists
        data = response.json() if response.content else None
        print(f"Error occurred: {data}")
        return False

###############################################
# Cleanup Operation
def profile_cleanup():
    # Get Profile IDs
    profile_ids = query_db()
    
    # Generate Jamf Pro API token
    token = generate_token()
    
    for profile_id in profile_ids:
        # Perform API operations with the token
        logger.info(f"Deleting profile with ID: {profile_id}")
        if delete_profile(token, profile_id):
            if update_deletion(profile_id):
                logger.info(f"Updated deletion timestamp for profile ID: {profile_id}")
            else:
                logger.error(f"Failed to update deletion timestamp for profile ID: {profile_id}")

###############################################
def run_cleaner():
    while True:
        try:
            profile_cleanup()
            print("checked for profiles...")
            time.sleep(30)  # Sleep for 30 seconds before the next iteration
        except Exception as e:
            logger.error(f"Error in cleaner script: {e}")
            time.sleep(60)  # If an error occurs, sleep for a minute before retrying

if __name__ == '__main__':
    run_cleaner()