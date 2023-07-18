#secret.py
from flask import Blueprint, request, jsonify, current_app
import time
from services import get_computer_id, generate_secret, store_secret, get_secret, create_and_scope_profile, get_secret_expiration

secrets_bp = Blueprint('secrets', __name__)

@secrets_bp.route('/secret', methods=['POST'])
def new_secret():
    udid = request.form.get('udid')
    
    existing_secret = get_secret(udid)
    if existing_secret and existing_secret['expiration'] > time.time():
        return jsonify({'message': 'A secret already exists for this computer'})
    
    # Step 1: Fetch the Computer ID from Jamf Pro using the UDID
    computer_id = get_computer_id(udid)

    if computer_id:
        # Step 2: Generate a secret
        secret = generate_secret()

        # Step 3: Store secret, udid, computer_id, and expiration date in the database
        expiration = store_secret(udid, computer_id, secret)

        # Step 4: Create and scope a configuration profile in Jamf Pro
        profile_name = f"Computer ID {computer_id}"
        category_id = current_app.config['CATEGORY_ID']

        # Create and scope a configuration profile in Jamf Pro
        result = create_and_scope_profile(computer_id, secret, expiration, category_id, profile_name)

        # If a profile with the same name already exists
        if 'error' in result:
            # Return a JSON response indicating that a profile with this name already exists
            return jsonify(result)

        return jsonify({'success': True})

    return jsonify({'error': 'Failed to generate secret'})


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