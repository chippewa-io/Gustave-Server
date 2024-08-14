from flask import Blueprint, jsonify, request, current_app
import requests
import xml.etree.ElementTree as ET
from services import mysql, generate_jamf_pro_token

computers_bp = Blueprint('computers', __name__)

###############################################
# Route to get computer details by UDID and secret
@computers_bp.route('/computers', methods=['POST'])
def get_computer_by_id():
    try:
        ###############################################
        # Get UDID and Secret from client request
        udid = request.json.get('udid')
        secret = request.json.get('secret')

        ###############################################
        # Query the database for the computer ID
        conn = mysql.connect()
        cur = conn.cursor()

        query = """
        SELECT computer_id 
        FROM secret_table 
        WHERE udid = %s AND secret = %s AND expiration > UNIX_TIMESTAMP()
        """
        cur.execute(query, (udid, secret))
        result = cur.fetchone()

        if result is None:
            return jsonify({'error': 'No computer found with the provided UDID and secret'}), 404

        computer_id = result[0]
        jamf_pro_url = current_app.config.get('JAMF_PRO_URL')
        ###############################################
        # Get the authentication token
        token = generate_jamf_pro_token()
        if token is None:
            return jsonify({'error': 'Failed to generate Jamf Pro token'}), 500

        ###############################################
        # Make the API request to Jamf Pro
        url = f"{jamf_pro_url}/api/v1/computers-inventory-detail/{computer_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return jsonify({'error': f'Jamf Pro API request failed with status code {response.status_code}'}), response.status_code

        response_data = response.json()
        return jsonify(response_data)

    except Exception as e:
        # Handle unexpected exceptions
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

###############################################
# Route to update computer details
@computers_bp.route('/computers/update', methods=['POST'])
def update_computer():
    try:
        ###############################################
        # Get UDID, Secret, ID, and Value from client request
        udid = request.json.get('udid')
        secret = request.json.get('secret')
        id = request.json.get('id')
        value = request.json.get('value')

        ###############################################
        # Query the database for the computer ID
        conn = mysql.connect()
        cur = conn.cursor()

        query = """
        SELECT computer_id 
        FROM secret_table 
        WHERE udid = %s AND secret = %s AND expiration > UNIX_TIMESTAMP()
        """
        cur.execute(query, (udid, secret))
        result = cur.fetchone()

        if result is None:
            return jsonify({'error': 'No computer found with the provided UDID and secret'}), 404

        computer_id = result[0]
        jamf_pro_url = current_app.config.get('JAMF_PRO_URL')
        
        ###############################################
        # Get the authentication token
        token = generate_jamf_pro_token()
        if token is None:
            return jsonify({'error': 'Failed to generate Jamf Pro token'}), 500

        ###############################################
        # Construct the XML data for the Jamf Pro API request
        root = ET.Element("computer")
        extension_attributes = ET.SubElement(root, "extension_attributes")
        extension_attribute = ET.SubElement(extension_attributes, "extension_attribute")
        ET.SubElement(extension_attribute, "id").text = id
        ET.SubElement(extension_attribute, "value").text = value
        xml_data = ET.tostring(root, encoding="utf-8", method="xml")

        # Convert the XML tree to a string including the XML declaration
        f = io.BytesIO()
        tree = ET.ElementTree(root)
        tree.write(f, encoding='utf-8', xml_declaration=True)
        xml_data = f.getvalue()

        ###############################################
        # Make the PUT request to update the computer record
        url = f"{jamf_pro_url}/JSSResource/computers/id/{computer_id}"
        headers = {
            'Accept': 'application/xml',
            'Content-Type': 'application/xml',
            'Authorization': f'Bearer {token}',
        }
        response = requests.put(url, headers=headers, data=xml_data)

        if response.status_code not in [200, 201]:
            return jsonify({'error': f'Update failed with status code {response.status_code}'}), response.status_code

        # Successful update
        return jsonify({'message': 'Update successful'})

    except Exception as e:
        # Handle unexpected exceptions
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500