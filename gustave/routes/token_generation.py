from flask import current_app
from flask import Blueprint, jsonify, request
import hashlib
import secrets
import requests
import base64
import xml.etree.ElementTree as ET
import subprocess


token_generation_bp = Blueprint('token_generation', __name__)

@token_generation_bp.route('/generate-token', methods=['POST'])

def generate_token():
    udid = request.form.get('udid')

    # Step 1: Fetch the Computer ID from Jamf Pro using the UDID
    computer_id = get_computer_id(udid)

    if computer_id:
        # Step 2: Generate a token/hash/certificate
        token = generate_token_hash()

        # Step 3: Create a configuration profile in Jamf Pro and scope it to the Computer ID
        success = create_configuration_profile(token, computer_id)

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to create configuration profile'})

    return jsonify({'error': 'Failed to generate token'})

def get_computer_id(udid):
    jamf_pro_url = current_app.config.get('JAMF_PRO_URL')
    jamf_pro_username = current_app.config.get('JAMF_PRO_USERNAME')
    jamf_pro_password = current_app.config.get('JAMF_PRO_PASSWORD')

    if not jamf_pro_url:
        return 'Jamf Pro URL is not configured'

    url = f"{jamf_pro_url}/JSSResource/computers/udid/{udid}"
    headers = {
        "Accept": "application/json"
    }
    response = requests.get(url, auth=(jamf_pro_username, jamf_pro_password), headers=headers)

    if response.status_code == 200:
        computer_data = response.json().get('computer')
        computer_id = computer_data.get('general').get('id')
        return computer_id

    return 'Failed to fetch computer ID'


def generate_token_hash():
    # Generate a unique secret/token/hash/certificate
    token = secrets.token_hex(32)
    return token

#def create_configuration_profile(token, computer_id):
    # Get the configuration values
    jamfProURL = current_app.config.get('JAMF_PRO_URL')
    jamfProUser = current_app.config.get('JAMF_PRO_USERNAME')
    jamfProPass = current_app.config.get('JAMF_PRO_PASSWORD')
    apiEndPoint = "JSSResource/osxconfigurationprofiles/id/0" # id/0 to create new profile
    category_id = current_app.config.get('CATEGORY_ID', -1)
    category_name = current_app.config.get('CATEGORY_NAME', 'No category assigned')
    name = "Gustave Test"
    secret = token

    # Call the bash script with all the necessary arguments
    subprocess.call(["/home/chris/gustave/profileCreation.sh", jamfProURL, jamfProUser, jamfProPass, name, secret, str(category_id), str(computer_id), str(computer_id)])

    # You can add error handling here to check if the bash script executed successfully
