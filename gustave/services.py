import requests
import datetime
import secrets
import time
import logging
import mysql.connector as mysql_connector
import xml.etree.ElementTree as ET
from threading import Lock
from flask_mysqldb import MySQL
from flask import current_app

###############################################
# Logging Configuration
logging.basicConfig(level=logging.INFO)

###############################################
# MySQL Connection
mysql = MySQL()

###############################################
# Initialize the database with the given Flask app
def init_db(app):
    mysql.init_app(app)

###############################################
# Store the generated secret in the database
def store_secret(udid, computer_id, secret):
    conn = mysql.get_db()
    cursor = conn.cursor()

    now = datetime.datetime.now()
    token_expiration_seconds = current_app.config['TOKEN_EXPIRATION']
    expiration_time = now + datetime.timedelta(seconds=token_expiration_seconds)
    expiration_timestamp = int(expiration_time.timestamp())

    # Check if a record with this UDID already exists
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
    cursor.execute(insert_query, (udid, computer_id, secret, expiration_timestamp))
    conn.commit()
    cursor.close()

    return expiration_timestamp

###############################################
# Retrieve the Computer ID from Jamf Pro using the UDID
def get_computer_id(udid):
    logging.info(f"Fetching Computer ID for UDID: {udid}")

    # Generate the token
    token = generate_jamf_pro_token()

    # Prepare the URL
    url = f"{current_app.config['JAMF_PRO_URL']}/JSSResource/computers/udid/{udid}"
    desired_group = current_app.config['SMART_GROUP']

    # Set the headers with the token
    headers = {
        "Accept": "application/xml",
        "Authorization": f"Bearer {token}"
    }

    # Make the request
    response = requests.get(url, headers=headers)

    logging.debug(f"Request URL: {url}")
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
        logging.debug("Checking for smart group membership...")
        group_memberships = root.find(".//computer_group_memberships")
        for group in group_memberships.findall("group"):
            if group.text == desired_group:
                return computer_id  # Found the group, return the ID

        raise Exception(f"Computer not in the desired group: {desired_group}")

    except ET.ParseError as e:
        error_message = f"Failed to parse XML response: {e}"
        logging.error(error_message)
        raise Exception(error_message)

    except AttributeError as e:
        error_message = f"Failed to find the required XML elements: {e}"
        logging.error(error_message)
        raise Exception(error_message)

###############################################
# Generate a secure secret
def generate_secret():
    return secrets.token_hex(16)

###############################################
# Retrieve the secret and its expiration for a given UDID
def get_secret(udid):
    conn = mysql.get_db()
    cursor = conn.cursor()

    query = "SELECT secret, expiration FROM secret_table WHERE udid = %s AND is_active = TRUE"
    cursor.execute(query, (udid,))
    result = cursor.fetchone()

    cursor.close()

    if result:
        return {'secret': result[0], 'expiration': result[1]}
    else:
        return None

###############################################
# Generate a Jamf Pro API token
def generate_jamf_pro_token():
    url = f"{current_app.config['JAMF_PRO_URL']}/api/oauth/token"
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

    logging.debug(f"Request URL: {url}")
    logging.debug(f"Response Status Code: {response.status_code}")
    logging.debug(f"Response Content: {response.content}")

    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f"Failed to generate Jamf Pro API token: {response.content}")

###############################################
# Extract the profile ID from the provided XML string
def extract_profile_id(xml_string):
    try:
        root = ET.fromstring(xml_string)
        return root.find('id').text
    except ET.ParseError:
        logging.error(f"XML parsing error. XML string:\n{xml_string}")
        return None

###############################################
# Create the XML payload for the configuration profile
def create_payload_xml(profile_name, secret, expiration):
    root = ET.Element("plist", version="1.0")

    # Build the XML structure
    dict_elem = ET.SubElement(root, "dict")
    ET.SubElement(dict_elem, "key").text = "PayloadUUID"
    ET.SubElement(dict_elem, "string").text = "42884445-1B56-4EA4-A3D6-7009702F5CC7"
    # (Other XML elements continue here)

    xml_string = ET.tostring(root).decode()
    xml_string = xml_string.replace("<", "&lt;").replace(">", "&gt;")

    return xml_string

###############################################
# Create and scope a configuration profile in Jamf Pro
def create_configuration_profile(jamfProURL, profile_name, secret, expiration, category_id, computer_id):
    token = generate_jamf_pro_token()
    payloadXML = create_payload_xml(profile_name, secret, expiration)

    configProfileXML = f"""
    <os_x_configuration_profile>
        <general>
            <name>{profile_name}</name>
            <description>Test Profile</description>
            <category>
                <id>{category_id}</id>
            </category>
            <distribution_method>Install Automatically</distribution_method>
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

    headers = {
        "Content-Type": "application/xml",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(f"{jamfProURL}/JSSResource/osxconfigurationprofiles/id/0", data=configProfileXML, headers=headers)

    logging.debug(f"Response Status Code: {response.status_code}")
    logging.debug(f"Response Content: {response.content.decode()}")

    if response.status_code == 201:
        root = ET.fromstring(response.content)
        profile_id = root.find("id").text
        store_profile(profile_id, computer_id)
        return {"success": True, "profile_id": profile_id}
    else:
        try:
            error_response = response.json()
        except ValueError:
            error_response = {"error": "Unable to parse response"}

        return {"error": error_response}

###############################################
# Store the profile ID in the database
def store_profile(profile_id, computer_id):
    conn = mysql.get_db()
    cursor = conn.cursor()
    logging.info(f"Storing profile {profile_id} for computer {computer_id}")

    query = "INSERT INTO active_profiles (profile_id, computer_id) VALUES (%s, %s)"
    cursor.execute(query, (profile_id, computer_id))
    conn.commit()
    cursor.close()

###############################################
# Retrieve a computer record from Jamf Pro using its ID
def retrieve_computer_record(computer_id):
    logging.info(f"Retrieving computer record for ID: {computer_id}")
    
    # Generate the token
    token = generate_jamf_pro_token()

    # Prepare the URL
    url = f"{current_app.config['JAMF_PRO_URL']}/JSSResource/computers/id/{computer_id}"

    # Set the headers with the token
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Make the request
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get('computer')

    logging.error(f"Failed to retrieve computer record. Status code: {response.status_code}")
    return None

###############################################
# Check for expired secrets and handle them
def check_for_expired_secrets():
    logging.info("Checking for expired secrets...")
    
    now = int(time.time())  # Get the current time as a Unix timestamp

    # Connect to the MySQL database
    conn = mysql.get_db()
    cursor = conn.cursor()

    # Query the database for expired secrets
    query = "SELECT * FROM secrets WHERE expiration < %s"
    cursor.execute(query, (now,))
    expired_secrets = cursor.fetchall()

    for secret in expired_secrets:
        unscope_and_delete_profiles(secret)

    cursor.close()
    conn.close()

###############################################
# Get a list of computer IDs with expired secrets
def get_expired_computer_ids():
    logging.info("Retrieving computer IDs with expired secrets...")

    conn = mysql_connector.connect(
        user=current_app.config['MYSQL_DATABASE_USER'],
        password=current_app.config['MYSQL_DATABASE_PASSWORD'],
        host=current_app.config['MYSQL_DATABASE_HOST'],
        database=current_app.config['MYSQL_DATABASE_DB']
    )

    current_time = int(time.time())
    query = f"SELECT computer_id FROM secret_table WHERE expiration < {current_time}"
    cursor = conn.cursor()
    cursor.execute(query)
    expired_computer_ids = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return expired_computer_ids

###############################################
# Get profile IDs that are scoped to the given computer IDs
def get_scoped_profile_ids(computer_ids):
    if not computer_ids:
        logging.info("No computer IDs provided.")
        return []

    logging.info("Retrieving scoped profile IDs for given computer IDs...")

    conn = mysql_connector.connect(
        user=current_app.config['MYSQL_DATABASE_USER'],
        password=current_app.config['MYSQL_DATABASE_PASSWORD'],
        host=current_app.config['MYSQL_DATABASE_HOST'],
        database=current_app.config['MYSQL_DATABASE_DB']
    )

    computer_ids_str = ', '.join(str(computer_id) for computer_id in computer_ids)
    query = f"SELECT profile_id FROM active_profiles WHERE computer_id IN ({computer_ids_str})"
    cursor = conn.cursor()
    cursor.execute(query)
    scoped_profile_ids = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return scoped_profile_ids

###############################################
# Move profiles from active to expired
def move_profiles(profile_id):
    logging.info(f"Moving profile {profile_id} from active to expired...")

    conn = mysql_connector.connect(
        user=current_app.config['MYSQL_DATABASE_USER'],
        password=current_app.config['MYSQL_DATABASE_PASSWORD'],
        host=current_app.config['MYSQL_DATABASE_HOST'],
        database=current_app.config['MYSQL_DATABASE_DB']
    )

    try:
        conn.start_transaction()

        query = "SELECT profile_id, computer_id FROM active_profiles WHERE profile_id = %s"
        cursor = conn.cursor()
        cursor.execute(query, (profile_id,))
        result = cursor.fetchall()

        for row in result:
            insert_query = "INSERT INTO expired_profiles (profile_id, computer_id) VALUES (%s, %s)"
            cursor.execute(insert_query, row)
            logging.info(f"Moved profile {row[0]} to the expired_profiles table.")

        delete_query = "DELETE FROM active_profiles WHERE profile_id = %s"
        cursor.execute(delete_query, (profile_id,))

        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Error moving profiles: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

###############################################
# Unscope a profile in Jamf Pro
def unscope_profile(profile_id):
    logging.info(f"Unscoping profile {profile_id}...")

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
            <exclusions>
                <computers/>
            </exclusions>
        </scope>
    </os_x_configuration_profile>
    """

    response = requests.put(url, headers=headers, data=data)

    if response.status_code in [200, 201]:
        logging.info(f"Successfully unscoped profile with ID {profile_id}.")
        move_profiles(profile_id)
    else:
        logging.error(f"Failed to unscope profile {profile_id}. Status code: {response.status_code}")

###############################################
# Delete profiles for a given UDID
def delete_profiles_for_udid(udid):
    logging.info(f"Deleting profiles for UDID: {udid}")
    
    computer_id = get_computer_id(udid)
    if not computer_id:
        return {"error": "No computer found for the given UDID"}, 404

    profile_ids = get_scoped_profile_ids([computer_id])
    if not profile_ids:
        return {"message": "No profiles found for the given computer ID"}, 200

    for profile_id in profile_ids:
        unscope_profile(profile_id)

    return {"message": "Profile deletion scheduled for all profiles of the given computer ID"}, 200

###############################################
# Check if a profile with the given name exists
def check_for_existing_profile(profile_name):
    logging.info(f"Checking if profile '{profile_name}' exists in Jamf Pro...")

    url = f"{current_app.config['JAMF_PRO_URL']}/JSSResource/osxconfigurationprofiles"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {generate_jamf_pro_token()}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        for profile in data['os_x_configuration_profiles']:
            if profile['name'] == profile_name:
                return profile

    logging.warning(f"Profile '{profile_name}' not found or request failed with status code {response.status_code}.")
    return None

###############################################
# Get the expiration date of a secret
def get_secret_expiration(secret):
    logging.info(f"Retrieving expiration date for secret: {secret}")
    
    conn = mysql.get_db()
    cursor = conn.cursor()

    query = "SELECT expiration FROM secret_table WHERE secret = %s"
    cursor.execute(query, (secret,))
    result = cursor.fetchone()

    cursor.close()

    if result:
        return {'expiration': result[0]}
    else:
        logging.warning(f"No expiration found for secret: {secret}")
        return None

###############################################
# Check if a profile with the given ID exists in Jamf Pro
def check_for_existing_profile_id(profile_id):
    logging.info(f"Checking if profile with ID '{profile_id}' exists in Jamf Pro...")

    url = f"{current_app.config['JAMF_PRO_URL']}/JSSResource/osxconfigurationprofiles/id/{profile_id}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {generate_jamf_pro_token()}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True

    logging.warning(f"Profile with ID '{profile_id}' not found or request failed with status code {response.status_code}.")
    return False