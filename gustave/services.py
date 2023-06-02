import requests
import datetime
import secrets
import subprocess
import time
import mysql.connector as mysql_connector
import xml.etree.ElementTree as ET
from flaskext.mysql import MySQL
from flask import current_app
from config import Config
from flask import Flask
import gustave.config as config



#MySQL Connection
mysql = MySQL()

def init_db(app):
    mysql.init_app(app)

#For storing the generated secrets in our database
def store_secret(udid, computer_id, secret):
    conn = mysql.get_db()
    cursor = conn.cursor()

    now = datetime.datetime.now()
    token_expiration_seconds = current_app.config['TOKEN_EXPIRATION']
    expiration_time = now + datetime.timedelta(seconds=token_expiration_seconds)
    expiration_timestamp = int(expiration_time.timestamp())

    query = "INSERT INTO secret_table (udid, computer_id, secret, expiration) VALUES (%s, %s, %s, %s)"
    values = (udid, computer_id, secret, expiration_timestamp)
    try:
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
    except mysql_connector.Error as e:
        current_app.logger.error('Failed to store secret in database: %s', e)
        return None

#For collecting the Computer ID from Jamf Pro, to be stored in the database
def get_computer_id(udid):
    url = current_app.config['JAMF_PRO_URL'] + '/JSSResource/computers/udid/' + udid
    username = current_app.config['JAMF_PRO_USERNAME']
    password = current_app.config['JAMF_PRO_PASSWORD']

    headers = {"Accept": "application/json"}
    response = requests.get(url, auth=(username, password), headers=headers)

    if response.status_code == 200:
        computer_data = response.json().get('computer')
        computer_id = computer_data.get('general').get('id')
        return computer_id
    else:
        error_message = f"Failed to retrieve computer ID. Status code: {response.status_code}"
        raise Exception(error_message)

def generate_secret():
    secret = secrets.token_hex(16)
    return secret

def generate_token_hash():
    token = secrets.token_hex(32)
    return token

def get_secret(udid):
    conn = mysql.get_db()
    cursor = conn.cursor()

    query = "SELECT secret FROM secret_table WHERE udid = %s AND expiration > UNIX_TIMESTAMP()"
    values = (udid,)
    cursor.execute(query, values)
    result = cursor.fetchone()

    cursor.close()

    if result:
        return result[0]
    else:
        return None

def generate_jamf_pro_token():
    url = f"{Config.JAMF_PRO_URL}/uapi/auth/tokens"
    auth = (Config.JAMF_PRO_USERNAME, Config.JAMF_PRO_PASSWORD)
    headers = {"Accept": "application/json"}

    response = requests.post(url, auth=auth, headers=headers)

    if response.status_code == 200:
        jamfToken = response.json().get('token')
        return jamfToken
    else:
        raise Exception(f"Failed to generate Jamf Pro API token: {response.content}")

def extract_profile_id(xml_string):
    root = ET.fromstring(xml_string)
    profile_id = root.find('id').text
    return profile_id

def create_and_scope_profile(computer_id, secret, category_id, profile_name):
    jamfProURL = current_app.config['JAMF_PRO_URL']
    jamfProUser = current_app.config['JAMF_PRO_USERNAME']
    jamfProPass = current_app.config['JAMF_PRO_PASSWORD']

    # Command to execute the bash script with the provided arguments
    command = f'resources/profile_create.sh "{jamfProURL}" "{jamfProUser}" "{jamfProPass}" "{profile_name}" "{secret}" "{category_id}" "{computer_id}"'

    try:
        # Execute the command
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)

        # Capture the ID of the profile we're creating
        script_output = result.stdout
        #print(f"Script output: {script_output}")
        # Extract the profile ID from the output
        profile_id = extract_profile_id(script_output)
        print(f"Extracted profile ID: {profile_id}")
        #send it to the database
        store_profile(profile_id, computer_id)
        # Print the standard error
        script_error = result.stderr
        #print(f"Script error: {script_error}")
       
        return script_output
    
    except subprocess.CalledProcessError as e:
        error_message = e.stderr
        # Handle the error

def store_profile(profile_id, computer_id):
    conn = mysql.get_db()
    cursor = conn.cursor()
    print(f"MySQL Query: {profile_id, computer_id}")
    query = "INSERT INTO active_profiles (profile_id, computer_id) VALUES (%s, %s)"
    values = (profile_id, computer_id)

    cursor.execute(query, values)
    conn.commit()
    cursor.close()

def retrieve_computer_record(computer_id):
    url = current_app.config['JAMF_PRO_URL'] + f'/JSSResource/computers/id/{computer_id}'
    username = current_app.config['JAMF_PRO_USERNAME']
    password = current_app.config['JAMF_PRO_PASSWORD']

    headers = {"Accept": "application/json"}
    response = requests.get(url, auth=(username, password), headers=headers)

    if response.status_code == 200:
        computer_record = response.json().get('computer')
        return computer_record

    return None

def check_for_expired_secrets():
    # Get the current time as a Unix timestamp
    now = int(time.time())

    # Create a connection to your MySQL database
    conn = mysql.connect()
    cursor = conn.cursor()

    # Query the database for secrets that are expired
    query = "SELECT * FROM secrets WHERE expiration < %s"
    cursor.execute(query, (now,))

    # Now you have a list of expired secrets
    # You can pass these to another function to unscope and delete the corresponding profiles
    expired_secrets = cursor.fetchall()
    for secret in expired_secrets:
        unscope_and_delete_profiles(secret)

    cursor.close()
    conn.close()

def get_expired_computer_ids():
    app = Flask(__name__)
    app.config.from_object(current_app.config['CONFIG_CLASS'])

    with app.app_context():
        # Connect to MySQL database
        conn = mysql_connector.connect(
            user=app.config['MYSQL_DATABASE_USER'],
            password=app.config['MYSQL_DATABASE_PASSWORD'],
            host=app.config['MYSQL_DATABASE_HOST'],
            database=app.config['MYSQL_DATABASE_DB']
        )

        # Get current timestamp
        current_time = int(time.time())

        # Query the secret_table for computer IDs with expired secrets
        query = f"SELECT computer_id FROM secret_table WHERE expiration < {current_time}"
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()

        # Close database connection
        conn.close()

        # Extract the computer IDs from the query result
        expired_computer_ids = [row[0] for row in result]

        return expired_computer_ids

def get_scoped_profile_ids(computer_ids):
    if not computer_ids:
        return []
    app = Flask(__name__)
    app.config.from_object(current_app.config['CONFIG_CLASS'])

    with app.app_context():
        # Connect to MySQL database
        conn = mysql_connector.connect(
            user=app.config['MYSQL_DATABASE_USER'],
            password=app.config['MYSQL_DATABASE_PASSWORD'],
            host=app.config['MYSQL_DATABASE_HOST'],
            database=app.config['MYSQL_DATABASE_DB']
        )

        # Query the active_profiles table for profile IDs scoped to the given computer IDs
        computer_ids_str = ', '.join(str(computer_id) for computer_id in computer_ids)
        query = f"SELECT profile_id FROM active_profiles WHERE computer_id IN ({computer_ids_str})"
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()

        # Close database connection
        conn.close()

        # Extract the profile IDs from the query result
        scoped_profile_ids = [row[0] for row in result]

        return scoped_profile_ids

def unscope_profile(profile_id):
    token = generate_jamf_pro_token()
    url = f"{current_app.config['JAMF_PRO_URL']}/JSSResource/osxconfigurationprofiles/id/{profile_id}"
    headers = {
        "Accept": "application/xml",
        "Content-Type": "application/xml",
        "Authorization": f"Bearer {token}"
    }

    data = """
<os_x_configuration_profile>
    <scope>
        <all_computers>false</all_computers>
        <all_jss_users>false</all_jss_users>
        <buildings/>
        <departments/>
        <computer_groups/>
        <jss_users/>
        <jss_user_groups/>
        <limitations>
            <users/>
            <user_groups/>
            <network_segments/>
            <ibeacons/>
        </limitations>
        <exclusions>
            <computers/>
            <buildings/>
            <departments/>
            <computer_groups/>
            <users/>
            <user_groups/>
            <network_segments/>
            <ibeacons/>
            <jss_users/>
            <jss_user_groups/>
        </exclusions>
    </scope>
</os_x_configuration_profile>
    """

    response = requests.put(url, headers=headers, data=data)

    if response.status_code in [200, 201]:
        print(f"Successfully unscoped profile with ID {profile_id}.")
        move_profiles(profile_id)

        # Additional DELETE request
        delete_response = requests.delete(url, headers=headers)

        if delete_response.status_code == 200:
            print(f"Successfully deleted profile with ID {profile_id}.")
        else:
            print(f"Failed to delete profile with ID {profile_id}. Status code: {delete_response.status_code}, Response: {delete_response.text}")

    else:
        print(f"Failed to unscope profile with ID {profile_id}. Status code: {response.status_code}, Response: {response.text}")

def move_profiles(profile_id):
    app = Flask(__name__)
    app.config.from_object(current_app.config['CONFIG_CLASS'])

    with app.app_context():
        # Connect to MySQL database
        conn = mysql_connector.connect(
            user=app.config['MYSQL_DATABASE_USER'],
            password=app.config['MYSQL_DATABASE_PASSWORD'],
            host=app.config['MYSQL_DATABASE_HOST'],
            database=app.config['MYSQL_DATABASE_DB']
        )

        # Move records from active_profiles to expired_profiles
        try:
            # Start a transaction
            conn.start_transaction()

            # Query the active_profiles table for the given profile ID
            query = f"SELECT profile_id, computer_id FROM active_profiles WHERE profile_id = {profile_id}"
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()

            # Move records to the expired_profiles table
            for row in result:
                profile_id, computer_id = row
                insert_query = f"INSERT INTO expired_profiles (profile_id, computer_id) VALUES ({profile_id}, {computer_id})"
                cursor.execute(insert_query)

            # Delete records from the active_profiles table
            delete_query = f"DELETE FROM active_profiles WHERE profile_id = {profile_id}"
            cursor.execute(delete_query)

            # Commit the transaction
            conn.commit()
        except Exception as e:
            # Rollback the transaction in case of any errors
            conn.rollback()
            raise e
        finally:
            # Close database connection
            conn.close()

        return

def cleanup_expired_profiles(app):
    with app.app_context():
        # Get the computer IDs from the secret_table where the expiration has passed
        expired_computer_ids = get_expired_computer_ids()

        # Query the active_profile table for profile IDs scoped to those computer IDs
        scoped_profile_ids = get_scoped_profile_ids(expired_computer_ids)

        # Unscope profiles
        for profile_id in scoped_profile_ids:
            unscope_profile(profile_id)
