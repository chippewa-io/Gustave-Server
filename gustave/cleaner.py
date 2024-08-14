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
# Setup Logging
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
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_DATABASE_HOST,
            user=Config.MYSQL_DATABASE_USER,
            password=Config.MYSQL_DATABASE_PASSWORD,
            database=Config.MYSQL_DATABASE_DB,
            port=Config.MYSQL_DATABASE_PORT
        )

        cursor = connection.cursor()
        current_epoch_timestamp = int(datetime.now().timestamp())
        query = f"SELECT profile_id FROM expired_profiles WHERE deletion < {current_epoch_timestamp}"
        cursor.execute(query)
        expired_profile_ids = [row[0] for row in cursor.fetchall()]
        return expired_profile_ids
    except mysql.connector.Error as err:
        logger.error(f"Error querying the database: {err}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def update_deletion(profile_id):
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_DATABASE_HOST,
            user=Config.MYSQL_DATABASE_USER,
            password=Config.MYSQL_DATABASE_PASSWORD,
            database=Config.MYSQL_DATABASE_DB,
            port=Config.MYSQL_DATABASE_PORT
        )

        cursor = connection.cursor()
        query = "UPDATE expired_profiles SET deletion = NULL WHERE profile_id = %s"
        cursor.execute(query, (profile_id,))
        connection.commit()

        if cursor.rowcount == 1:
            logger.info(f"Successfully updated deletion timestamp for profile ID: {profile_id}")
        else:
            logger.warning(f"Failed to update deletion timestamp for profile ID: {profile_id}")
    except mysql.connector.Error as err:
        logger.error(f"Error updating the database: {err}")
    finally:
        cursor.close()
        connection.close()

###############################################
# Jamf API operations
def delete_profile(profile_id):
    token = generate_jamf_pro_token()
    url = f"{JamfURL}/JSSResource/osxconfigurationprofiles/id/{profile_id}"
    headers = {
        "Accept": "application/xml",
        "Content-Type": "application/xml",
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.delete(url, headers=headers)
        if response.status_code in [200, 404]:
            logger.info(f"Successfully processed profile with ID: {profile_id}")
            return True
        else:
            logger.error(f"Error occurred: {response.json()}")
            return False
    except requests.RequestException as e:
        logger.error(f"Error contacting Jamf server: {e}")
        return False

###############################################
# Cleanup Operation
def profile_cleanup(app):
    with app.app_context():
        profile_ids = query_db()
        for profile_id in profile_ids:
            logger.info(f"Attempting to delete profile with ID: {profile_id}")
            if delete_profile(profile_id):
                try:
                    update_deletion(profile_id)
                except Exception as e:
                    logger.error(f"Failed to update deletion timestamp for profile ID: {profile_id}. Error: {e}")

###############################################
def run_cleaner(app):
    while True:
        try:
            profile_cleanup(app)
            logger.info("Checked for profiles...")
            time.sleep(30)  # Sleep for 30 seconds before the next iteration
        except Exception as e:
            logger.error(f"Error in cleaner script: {e}")
            time.sleep(60)  # If an error occurs, sleep for a minute before retrying