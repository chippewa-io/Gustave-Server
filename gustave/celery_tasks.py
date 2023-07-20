##############################################
# celery_tasks.py file
##############################################
import requests
import logging
from celery import Celery
import importlib.util
import os
import sys
from services import generate_jamf_pro_token

# Load config
sys.path.append('/etc/gustave')
# Add the path to the system path for direct imports
sys.path.append('/etc/gustave')
# Import the configuration
spec = importlib.util.spec_from_file_location('config', '/etc/gustave/config.py')
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
print(dir(config_module))
# Extract the values
JAMF_PRO_URL = config_module.Config.JAMF_PRO_URL
JAMF_PRO_USERNAME = config_module.Config.JAMF_PRO_USERNAME
JAMF_PRO_PASSWORD = config_module.Config.JAMF_PRO_PASSWORD
CELERY_BROKER_URL = config_module.Config.CELERY_BROKER_URL
CELERY_RESULT_BACKEND = config_module.Config.CELERY_RESULT_BACKEND

def generate_jamf_pro_token():
    url = JAMF_PRO_URL + '/uapi/auth/tokens'
    auth = (JAMF_PRO_USERNAME, JAMF_PRO_PASSWORD)
    headers = {"Accept": "application/json"}

    response = requests.post(url, auth=auth, headers=headers)

    if response.status_code == 200:
        jamfToken = response.json().get('token')
        return jamfToken
    else:
        logging.error(f"Failed to generate Jamf Pro API token: {response.content}")
        raise Exception(f"Failed to generate Jamf Pro API token: {response.content}")


# Create a Celery instance
celery = Celery(__name__)
celery.config_from_object('celeryconfig')
def init_celery(flask_app):
    """
    Initialize Celery with the Flask app context.
    """
    celery.config_from_object(flask_app.config)
    celery.conf.broker_url = flask_app.config['CELERY_BROKER_URL']
    celery.conf.result_backend = flask_app.config['CELERY_RESULT_BACKEND']
    
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

@celery.task
def delete_profile_after_delay(profile_id):
    print ("running... delete_profile_after_delay")
    token = generate_jamf_pro_token()
    url = JAMF_PRO_URL + '/JSSResource/osxconfigurationprofiles/id/' + profile_id
    headers = {
        "Accept": "application/xml",
        "Content-Type": "application/xml",
        "Authorization": f"Bearer {token}"
    }
    response = requests.delete(url, headers=headers)

    if response.status_code == 200:
        print(f"Successfully deleted profile with ID {profile_id}.")
    elif response.status_code == 404:
        print(f"Profile with ID {profile_id} not found. It may have already been deleted.")
    else:
        print(f"Failed to delete profile with ID {profile_id}. Status code: {response.status_code}, Response: {response.text}")

