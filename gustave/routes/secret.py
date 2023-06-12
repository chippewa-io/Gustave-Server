from flask import Blueprint, request, jsonify, current_app
import time
from services import get_computer_id, generate_secret, store_secret, get_secret, create_and_scope_profile

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
        create_and_scope_profile(computer_id, secret, expiration, category_id, profile_name)

        return jsonify({'success': True})

    return jsonify({'error': 'Failed to generate secret'})