import time
import sys
import mysql.connector
import logging
import logging.handlers
import requests
from datetime import datetime
from flask import current_app

# Adjust sys.path to find the config module
sys.path.append('/etc/gustave')
from gustave_config import ProductionConfig as Config
from services import generate_jamf_pro_token  # Import the token generation function

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
JamfURL = Config.JAMF_PRO_URL

###############################################
# Database operations
def query_db():
    # Establish the MySQL connection using credentials from config.py
    connection = mysql.connector.connect(
        host=Config.MYSQL_DATABASE_HOST,
        user=Config.MYSQL_DATABASE_USER,
        password=Config.MYSQL_DATABASE_PASSWORD,
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
        password=Config.MYSQL_DATABASE_PASSWORD,
        database=Config.MYSQL_DATABASE_DB,
        port=Config.MYSQL_DATABASE_PORT
    )

    cursor = connection.cursor()

    # Update the deletion timestamp to null for the profile ID
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
# Jamf API operations
def delete_profile(profile_id):
    token = generate_jamf_pro_token()
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
def profile_cleanup(app):
    with app.app_context():
        # Get Profile IDs
        profile_ids = query_db()
        
        for profile_id in profile_ids:
            # Perform API operations with the token
            print(f"Attempting to delete profile with ID: {profile_id}")
            if delete_profile(profile_id):
                try:
                    update_deletion(profile_id)
                    print(f"Updated deletion timestamp for profile ID: {profile_id}")
                except Exception as e:
                    print(f"Failed to update deletion timestamp for profile ID: {profile_id}. Error: {e}")

###############################################
def run_cleaner(app):
    while True:
        try:
            profile_cleanup(app)
            print("Checked for profiles...")
            time.sleep(30)  # Sleep for 30 seconds before the next iteration
        except Exception as e:
            print(f"Error in cleaner script: {e}")
            time.sleep(60)  # If an error occurs, sleep for a minute before retrying