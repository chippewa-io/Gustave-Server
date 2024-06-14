import requests
import datetime
import secrets
import time
import logging
import mysql.connector as mysql_connector
import xml.etree.ElementTree as ET
from threading import Lock
from flaskext.mysql import MySQL
from flask import Flask
import sys
import os
import importlib.util
from flask import current_app
##loging
logging.basicConfig(level=logging.INFO)


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

    # Check if a record with this udid already exists
    query = "SELECT * FROM secret_table WHERE udid = %s"
    cursor.execute(query, (udid,))
    existing_record = cursor.fetchone() 

    if existing_record:
        # If it exists, set its is_active flag to FALSE
        update_query = "UPDATE secret_table SET is_active = FALSE WHERE udid = %s"
        cursor.execute(update_query, (udid,))

    # Insert the new record (is_active will be TRUE by default)
    insert_query = """
        INSERT INTO secret_table (udid, computer_id, secret, expiration, is_active)
        VALUES (%s, %s, %s, %s, TRUE)
    """
    values = (udid, computer_id, secret, expiration_timestamp)
    cursor.execute(insert_query, values)
    conn.commit()
    cursor.close()


    return expiration_timestamp


#For collecting the Computer ID from Jamf Pro, to be stored in the database
def get_computer_id(udid):
    print("UDID from Gustave: " + udid)
    
    # Generate the token
    token = generate_jamf_pro_token()

    # Prepare the URL
    url = current_app.config['JAMF_PRO_URL'] + f'/JSSResource/computers/udid/{udid}'
    desired_group = current_app.config['SMART_GROUP']

    # Set the headers with the token
    headers = {
        "Accept": "application/xml",
        "Authorization": f"Bearer {token}"
    }

    # Make the request
    response = requests.get(url, headers=headers)

    # Log the request details
    logging.debug(f"Request URL: {url}")
    logging.debug(f"Request Headers: {headers}")
    logging.debug(f"Response Status Code: {response.status_code}")
    logging.debug(f"Response Content: {response.content}")

    if response.status_code != 200:
        error_message = f"Failed to retrieve computer info. Status code: {response.status_code}, Response: {response.content}"
        logging.error(error_message)
        raise Exception(error_message)

    try:
        # Parse the XML response
        root = ET.fromstring(response.text)
        computer_id = root.find(".//general/id").text

        # Check if the desired group is in the computer_group_memberships
        logging.debug("Searching for smart group membership...")
        group_memberships = root.find(".//computer_group_memberships")
        for group in group_memberships.findall("group"):
            if group.text == desired_group:
                return computer_id  # Found the group, return the ID

        # If the computer is not part of the desired group
        raise Exception(f"Computer not in the desired group: {desired_group}")
    
    except ET.ParseError as e:
        error_message = f"Failed to parse XML response: {e}"
        logging.error(error_message)
        raise Exception(error_message)
    except AttributeError as e:
        error_message = f"Failed to find the required XML elements: {e}"
        logging.error(error_message)
        raise Exception(error_message)

def generate_secret():
    secret = secrets.token_hex(16)
    return secret


def get_secret(udid):
    conn = mysql.get_db()
    cursor = conn.cursor()

    query = query = "SELECT secret, expiration FROM secret_table WHERE udid = %s AND is_active = TRUE"
    values = (udid,)
    cursor.execute(query, values)
    result = cursor.fetchone()

    cursor.close()

    if result:
        return {'secret': result[0], 'expiration': result[1]}
    else:
        return None

def generate_jamf_pro_token():
    url = current_app.config['JAMF_PRO_URL'] + "/api/oauth/token"
    client_id = current_app.config['JAMF_PRO_CLIENT_ID']
    client_secret = current_app.config['JAMF_PRO_CLIENT_SECRET']
    
    data = {
        'client_id': client_id,
        'grant_type': 'client_credentials',
        'client_secret': client_secret
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(url, data=data, headers=headers)
    
    # Debugging logs
    print("URL:", url)
    print("Data:", data)
    print("Response Status Code:", response.status_code)
    print("Response Content:", response.content)

    if response.status_code == 200:
        access_token = response.json().get('access_token')
        return access_token
    else:
        raise Exception(f"Failed to generate Jamf Pro API token: {response.content}")

def extract_profile_id(xml_string):
    # Try to parse the XML string
    try:
        root = ET.fromstring(xml_string)
        profile_id = root.find('id').text
        return profile_id
    except ET.ParseError:
        print(f"Yo, we've got an XML parsing error. Check out this XML string:\n{xml_string}")
        return None

def create_payload_xml(profile_name, secret, expiration):
    root = ET.Element("plist", version="1.0")

    dict_elem = ET.SubElement(root, "dict")
    ET.SubElement(dict_elem, "key").text = "PayloadUUID"
    ET.SubElement(dict_elem, "string").text = "42884445-1B56-4EA4-A3D6-7009702F5CC7"
    ET.SubElement(dict_elem, "key").text = "PayloadType"
    ET.SubElement(dict_elem, "string").text = "Configuration"
    ET.SubElement(dict_elem, "key").text = "PayloadOrganization"
    ET.SubElement(dict_elem, "string").text = "Jamf"
    ET.SubElement(dict_elem, "key").text = "PayloadIdentifier"
    ET.SubElement(dict_elem, "string").text = "42884445-1B56-4EA4-A3D6-7009702F5CC7"
    ET.SubElement(dict_elem, "key").text = "PayloadDisplayName"
    ET.SubElement(dict_elem, "string").text = profile_name
    ET.SubElement(dict_elem, "key").text = "PayloadDescription"
    ET.SubElement(dict_elem, "string").text = ""
    ET.SubElement(dict_elem, "key").text = "PayloadVersion"
    ET.SubElement(dict_elem, "integer").text = "1"
    ET.SubElement(dict_elem, "key").text = "PayloadEnabled"
    ET.SubElement(dict_elem, "true")
    ET.SubElement(dict_elem, "key").text = "PayloadRemovalDisallowed"
    ET.SubElement(dict_elem, "true")
    ET.SubElement(dict_elem, "key").text = "PayloadScope"
    ET.SubElement(dict_elem, "string").text = "System"
    ET.SubElement(dict_elem, "key").text = "PayloadContent"
    array_elem = ET.SubElement(dict_elem, "array")
    dict2_elem = ET.SubElement(array_elem, "dict")
    ET.SubElement(dict2_elem, "key").text = "PayloadDisplayName"
    ET.SubElement(dict2_elem, "string").text = "Custom Settings"
    ET.SubElement(dict2_elem, "key").text = "PayloadIdentifier"
    ET.SubElement(dict2_elem, "string").text = "D9A57B93-83DE-40C5-AF59-B3E17B76041A"
    ET.SubElement(dict2_elem, "key").text = "PayloadOrganization"
    ET.SubElement(dict2_elem, "string").text = "JAMF Software"
    ET.SubElement(dict2_elem, "key").text = "PayloadType"
    ET.SubElement(dict2_elem, "string").text = "com.apple.ManagedClient.preferences"
    ET.SubElement(dict2_elem, "key").text = "PayloadUUID"
    ET.SubElement(dict2_elem, "string").text = "D9A57B93-83DE-40C5-AF59-B3E17B76041A"
    ET.SubElement(dict2_elem, "key").text = "PayloadVersion"
    ET.SubElement(dict2_elem, "integer").text = "1"
    ET.SubElement(dict2_elem, "key").text = "PayloadContent"
    dict3_elem = ET.SubElement(dict2_elem, "dict")
    ET.SubElement(dict3_elem, "key").text = "io.chippewa.gustave"
    dict4_elem = ET.SubElement(dict3_elem, "dict")
    ET.SubElement(dict4_elem, "key").text = "Forced"
    array2_elem = ET.SubElement(dict4_elem, "array")
    dict5_elem = ET.SubElement(array2_elem, "dict")
    ET.SubElement(dict5_elem, "key").text = "mcx_preference_settings"
    dict6_elem = ET.SubElement(dict5_elem, "dict")
    ET.SubElement(dict6_elem, "key").text = "Secret"
    dict7_elem = ET.SubElement(dict6_elem, "dict")
    ET.SubElement(dict7_elem, "key").text = "Expiration"
    ET.SubElement(dict7_elem, "integer").text = str(expiration)
    ET.SubElement(dict7_elem, "key").text = "value"
    ET.SubElement(dict7_elem, "string").text = secret

    # Convert the XML structure to a string
    xml_string = ET.tostring(root).decode()
    
    # Escape the XML string
    xml_string = xml_string.replace("<", "&lt;").replace(">", "&gt;")
    
    return xml_string

def create_configuration_profile(jamfProURL, profile_name, secret, expiration, category_id, computer_id):
    # Generate a new token
    token = generate_jamf_pro_token()

    # Create the XML payload for the profile
    payloadXML = create_payload_xml(profile_name, secret, expiration)

    # Construct the larger XML structure for the configuration profile
    configProfileXML = f"""
    <os_x_configuration_profile>
        <general>
            <name>{profile_name}</name>
            <description>Test Profile</description>
            <site>
                <id>-1</id>
                <name>None</name>
            </site>
            <category>
                <id>{category_id}</id>
            </category>
            <distribution_method>Install Automatically</distribution_method>
            <user_removable>true</user_removable>
            <level>computer</level>
            <redeploy_on_update>Newly Assigned</redeploy_on_update>
            <payloads>{payloadXML}</payloads>
        </general>
        <scope>
            <computers>
                <computer>
                    <id>{computer_id}</id>
                </computer>
            </computers>
        </scope>
    </os_x_configuration_profile>
    """

    # Make the API call to Jamf Pro
    apiEndPoint = "JSSResource/osxconfigurationprofiles/id/0"
    headers = {
        "Content-Type": "application/xml",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(f"{jamfProURL}/{apiEndPoint}", data=configProfileXML, headers=headers)

    # Print the response for debugging
    print("Response Status Code:", response.status_code)
    print("Response Content:", response.content.decode())

    if response.status_code == 201:
        # Parse the XML response to get the profile ID
        root = ET.fromstring(response.content)
        profile_id = root.find("id").text

        # Store the profile ID in the database
        store_profile(profile_id, computer_id)
        return {"success": True, "profile_id": profile_id}
    else:
        try:
            error_response = response.json()
        except ValueError:
            error_response = {"error": "Unable to parse response"}

        return {"error": error_response}

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
    # Generate the token
    token = generate_jamf_pro_token()

    # Prepare the URL
    url = current_app.config['JAMF_PRO_URL'] + f'/JSSResource/computers/id/{computer_id}'

    # Set the headers with the token
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Make the request
    response = requests.get(url, headers=headers)

    # Check the response status
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
    # Connect to MySQL database
    conn = mysql_connector.connect(
        user=current_app.config['MYSQL_DATABASE_USER'],
        password=current_app.config['MYSQL_DATABASE_PASSWORD'],
        host=current_app.config['MYSQL_DATABASE_HOST'],
        database=current_app.config['MYSQL_DATABASE_DB']
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

    # Connect to MySQL database
    conn = mysql_connector.connect(
        user=current_app.config['MYSQL_DATABASE_USER'],
        password=current_app.config['MYSQL_DATABASE_PASSWORD'],
        host=current_app.config['MYSQL_DATABASE_HOST'],
        database=current_app.config['MYSQL_DATABASE_DB']
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

def move_profiles(profile_id):
    # Connect to MySQL database
    conn = mysql_connector.connect(
        user=current_app.config['MYSQL_DATABASE_USER'],
        password=current_app.config['MYSQL_DATABASE_PASSWORD'],
        host=current_app.config['MYSQL_DATABASE_HOST'],
        database=current_app.config['MYSQL_DATABASE_DB']
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
            # Logging the movement of the profile
            logging.info(f"Moved profile with ID {profile_id} to the expired_profiles table for deletion.")


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


def unscope_profile(profile_id):
    token = generate_jamf_pro_token()
    url = current_app.config['JAMF_PRO_URL'] + '/JSSResource/osxconfigurationprofiles/id/' + str(profile_id)

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

    else:
        print(f"Failed to unscope profile with ID {profile_id}. Status code: {response.status_code}, Response: {response.text}")


cleanup_lock = Lock()
processed_profiles = set()

# def cleanup_expired_profiles(app):
#     import logging
#     logger = logging.getLogger(__name__)
#     app.logger.info("cleanup_expired_profiles job triggered")
#     with app.app_context():
#         # Acquire the lock
#         if cleanup_lock.acquire(blocking=False):
#             # Get the computer IDs from the secret_table where the expiration has passed
#             expired_computer_ids = get_expired_computer_ids()

#             # Query the active_profile table for profile IDs scoped to those computer IDs
#             scoped_profile_ids = get_scoped_profile_ids(expired_computer_ids)

#             # Unscope and delete profiles
#             for profile_id in scoped_profile_ids[:]:
#                 if profile_id not in processed_profiles:
#                     # Check if the profile still exists in Jamf Pro
#                     logger.info(f"Checking for profile {profile_id} in Jamf Pro...")
#                     existing_profile = check_for_existing_profile_id(profile_id)

#                     if existing_profile:
#                         # Unscope the profile
#                         logger.info(f"found profile {profile_id} in Jamf Pro...")
#                         unscope_profile(profile_id)
#                         logger.info(f"unscoped profile {profile_id} in Jamf Pro...")
#                         # Wait for 600 seconds (10 minutes) to ensure that the profile has been unscoped and removed from the client machine.
#                         time.sleep(10)

#                         # Delete the profile
#                         delete_profile(profile_id)
#                         logger.info(f"deleted profile {profile_id} in Jamf Pro...")

#                         # Add the processed profile ID to the set
#                         processed_profiles.add(profile_id)
#                     else:
#                         # The profile doesn't exist, so we assume it has already been deleted
#                         logger.info(f"profile {profile_id} has already been removed from Jamf Pro...")
#                         # You may log a message or take appropriate action here if needed
#                         pass

#             # Release the lock
#             cleanup_lock.release()


def delete_profiles_for_udid(udid):
    # Get the computer ID for the given UDID
    computer_id = get_computer_id(udid)
    if not computer_id:
        return {"error": "No computer found for the given UDID"}, 404

    # Get the profile IDs for the given computer ID
    profile_ids = get_scoped_profile_ids([computer_id])
    if not profile_ids:
        return {"message": "No profiles found for the given computer ID"}, 200

    # Unscope and delete profiles
    for profile_id in profile_ids:
        unscope_profile(profile_id)


    return {"message": "Profile deletion scheduled for all profiles of the given computer ID"}, 200

def check_for_existing_profile(profile_name):
    # The base URL for the Jamf Pro API
    base_url = current_app.config['JAMF_PRO_URL']

    # The endpoint for getting configuration profiles
    endpoint = '/JSSResource/osxconfigurationprofiles'

    # The full URL for the API request
    url = base_url + endpoint

    # The headers for the API request
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {generate_jamf_pro_token()}'
    }

    # Send a GET request to the Jamf Pro API
    response = requests.get(url, headers=headers)

    # If the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Loop through each profile in the response
        for profile in data['os_x_configuration_profiles']:
            # If the profile's name matches the given profile name
            if profile['name'] == profile_name:
                # Return the profile
                return profile

    # If the request was not successful, or if no matching profile was found, return None
    return None

def get_secret_expiration(secret):
    conn = mysql.get_db()
    cursor = conn.cursor()

    query = "SELECT expiration FROM secret_table WHERE secret = %s"
    values = (secret,)
    cursor.execute(query, values)
    result = cursor.fetchone()

    cursor.close()

    if result:
        return {'expiration': result[0]}
    else:
        return None

def check_for_existing_profile_id(profile_id):
    # The base URL for the Jamf Pro API
    base_url = current_app.config['JAMF_PRO_URL']
    # The endpoint for getting configuration profiles
    endpoint = f'/JSSResource/osxconfigurationprofiles/id/{profile_id}'

    # The full URL for the API request
    url = base_url + endpoint

    # The headers for the API request
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {generate_jamf_pro_token()}'
    }

    # Send a GET request to the Jamf Pro API
    response = requests.get(url, headers=headers)

    # If the request was successful and the profile exists
    if response.status_code == 200:
        return True

    # If the request was not successful or the profile does not exist
    return False
