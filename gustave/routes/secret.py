from flask import Blueprint, request, jsonify, current_app
import time
from services import get_computer_id, generate_secret, store_secret, get_secret, create_configuration_profile, get_secret_expiration, generate_jamf_pro_token

secrets_bp = Blueprint('secrets', __name__)

###############################################
# Route to generate a new secret
@secrets_bp.route('/secret', methods=['POST'])
def new_secret():
    jamfProURL = current_app.config['JAMF_PRO_URL']
    udid = request.form.get('udid')

    # Check if a secret already exists for this computer and is still valid
    existing_secret = get_secret(udid)
    if existing_secret and existing_secret['expiration'] > time.time():
        return jsonify({'message': 'A secret already exists for this computer'})

    ###############################################
    # Step 1: Fetch the Computer ID from Jamf Pro using the UDID
    computer_id = get_computer_id(udid)

    if computer_id:
        ###############################################
        # Step 2: Generate a secret
        secret = generate_secret()

        ###############################################
        # Step 3: Store secret, udid, computer_id, and expiration date in the database
        expiration = store_secret(udid, computer_id, secret)

        ###############################################
        # Step 4: Create and scope a configuration profile in Jamf Pro
        profile_name = f"Computer ID {computer_id}"
        category_id = current_app.config['CATEGORY_ID']

        # Generate the Jamf Pro API token
        token = generate_jamf_pro_token()

        # Create and scope a configuration profile in Jamf Pro using the token
        result = create_configuration_profile(jamfProURL, profile_name, secret, expiration, category_id, computer_id)

        # Handle the case where a profile with the same name already exists
        if 'error' in result:
            return jsonify(result)

        return jsonify({'success': True})

    return jsonify({'error': 'Failed to generate secret'})

###############################################
# Route to obtain the expiration date of a secret
@secrets_bp.route('/secret/expiration', methods=['GET'])
def obtain_expiration():
    secret = request.args.get('secret')

    # Retrieve the expiration date for the provided secret
    expiration_info = get_secret_expiration(secret)
    if expiration_info:
        expiration_date = expiration_info['expiration']
        return jsonify({'expiration_date': expiration_date})
    else:
        return jsonify({'message': 'Secret not found or expired'})