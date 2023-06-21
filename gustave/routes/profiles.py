# routes/profiles.py
from flask import Blueprint, request
from services import delete_profiles_for_udid

profiles_bp = Blueprint('profiles', __name__)

@profiles_bp.route('/profiles', methods=['DELETE'])
def delete_profile_route():
    udid = request.args.get('udid')
    if udid:
        result = delete_profiles_for_udid(udid)
        return result
    else:
        return {"error": "No udid provided"}, 400
