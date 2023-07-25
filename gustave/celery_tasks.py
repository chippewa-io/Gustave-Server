import sys
import importlib.util
import requests
import logging
from celery import Celery

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

#celery = Celery()
celery = Celery(__name__, broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
def init_celery(flask_app):
    celery.config_from_object(flask_app.config)
    celery.conf.broker_url = CELERY_BROKER_URL
    celery.conf.result_backend = CELERY_RESULT_BACKEND
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask


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


@celery.task
def delete_profile_after_delay(profile_id):
    # Here, you should add the code to delete the profile in Jamf Pro.
    # This will depend on the API provided by Jamf Pro.
    # For example, you might need to send a DELETE request to a specific URL.
    # You might also need to include some headers in the request.
    # Here's a basic example:
    print ("running... delete_profile_after_delay")
    token = generate_jamf_pro_token()
    url = JAMF_PRO_URL + '/JSSResource/osxconfigurationprofiles/id/' + str(profile_id)
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


