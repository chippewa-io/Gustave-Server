from flask import Blueprint, request, jsonify
from services import delete_profiles_for_udid

profiles_bp = Blueprint('profiles', __name__)

###############################################
# Route to delete profiles associated with a UDID
@profiles_bp.route('/profiles', methods=['DELETE'])
def delete_profile_route():
    udid = request.args.get('udid')

    if not udid:
        return jsonify({"error": "No UDID provided"}), 400

    ###############################################
    # Call service to delete profiles based on UDID
    result = delete_profiles_for_udid(udid)

    return jsonify(result)