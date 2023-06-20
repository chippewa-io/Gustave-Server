from flask import Blueprint, jsonify, request, current_app
from flaskext.mysql import MySQL
import requests
from services import mysql
from services import generate_jamf_pro_token
import xml.etree.ElementTree as ET


computers_bp = Blueprint('computers', __name__)

@computers_bp.route('/computers', methods=['POST'])
def get_computer_by_id():
    try:
        # get UDID and Secret from client request
        udid = request.json.get('udid')
        secret = request.json.get('secret')

        # create a cursor for MySQL
        conn = mysql.connect()
        cur = conn.cursor()

        # execute query to get the computer ID by UDID and Secret
        query = "SELECT computer_id FROM secret_table WHERE udid = %s AND secret = %s AND expiration > UNIX_TIMESTAMP()"
        cur.execute(query, (udid, secret,))
        result = cur.fetchone()

        if result is None:
            return jsonify({'error': 'No computer found with the provided UDID and secret'})

        computer_id = result[0]
        jamf_pro_url = current_app.config.get('JAMF_PRO_URL')
        jamf_pro_username = current_app.config.get('JAMF_PRO_USERNAME')
        jamf_pro_password = current_app.config.get('JAMF_PRO_PASSWORD')

        # Get the authentication token
        token = generate_jamf_pro_token()

        if token is None:
            return jsonify({'error': 'Failed to generate Jamf Pro token'})

        # Make the API request to Jamf Pro using the retrieved token
        url = f"{jamf_pro_url}/JSSResource/computers/id/{computer_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return jsonify({'error': f'Jamf Pro API request failed with status code {response.status_code}'})

        response_data = response.json()
        return jsonify(response_data)

    except Exception as e:
        # Catch any other exceptions and return a generic error message
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'})

@computers_bp.route('/computers/update', methods=['POST'])
def update_computer():
    try:
        # get UDID, Secret, ID, and Value from client request
        udid = request.json.get('udid')
        secret = request.json.get('secret')
        id = request.json.get('id')
        value = request.json.get('value')

        # create a cursor for MySQL
        conn = mysql.connect()
        cur = conn.cursor()

        # execute query to get the computer ID by UDID and Secret
        query = "SELECT computer_id FROM secret_table WHERE udid = %s AND secret = %s AND expiration > UNIX_TIMESTAMP()"
        cur.execute(query, (udid, secret,))
        result = cur.fetchone()

        if result is None:
            return jsonify({'error': 'No computer found with the provided UDID and secret'})

        computer_id = result[0]
        jamf_pro_url = current_app.config.get('JAMF_PRO_URL')
        jamf_pro_username = current_app.config.get('JAMF_PRO_USERNAME')
        jamf_pro_password = current_app.config.get('JAMF_PRO_PASSWORD')

        # Get the authentication token
        token = generate_jamf_pro_token()

        if token is None:
            return jsonify({'error': 'Failed to generate Jamf Pro token'})

        # Construct the XML data
        root = ET.Element("computer")
        extension_attributes = ET.SubElement(root, "extension_attributes")
        extension_attribute = ET.SubElement(extension_attributes, "extension_attribute")
        ET.SubElement(extension_attribute, "id").text = id
        ET.SubElement(extension_attribute, "value").text = value
        xml_data = ET.tostring(root, encoding="utf-8", method="xml")

        # Construct the headers
        headers = {
            'Accept': 'application/xml',
            'Content-Type': 'application/xml',
            'Authorization': f'Bearer {token}',
        }

        # Send the PUT request
        url = f"{jamf_pro_url}/JSSResource/computers/id/{computer_id}"
        print(f"URL: {url}")
        print(f"Headers: {headers}")
        print(f"Data: {xml_data.decode('utf-8')}")
        response = requests.put(url, headers=headers, data=xml_data)

        if response.status_code != 200:
            return jsonify({'error': f'Jamf Pro API request failed with status code {response.status_code}'})

        # Return the response
        return jsonify(response.json())

    except Exception as e:
        # Catch any other exceptions and return a generic error message
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'})
