import sys
import os
import importlib.util
from celery import Celery
from app import app
from services import generate_jamf_pro_token

# Load config
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append('/etc/gustave')
spec = importlib.util.spec_from_file_location('config', '/etc/gustave/config.py')
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

def generate_jamf_pro_token():
    url = app.config['JAMF_PRO_URL'] + '/uapi/auth/tokens'
    auth = (app.config['JAMF_PRO_USERNAME'], app.config['JAMF_PRO_PASSWORD'])
    headers = {"Accept": "application/json"}

    response = requests.post(url, auth=auth, headers=headers)

    if response.status_code == 200:
        jamfToken = response.json().get('token')
        return jamfToken
    else:
        logging.error(f"Failed to generate Jamf Pro API token: {response.content}")
        raise Exception(f"Failed to generate Jamf Pro API token: {response.content}")


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)

@celery.task
def delete_profile_after_delay(profile_id):
    # Here, you should add the code to delete the profile in Jamf Pro.
    # This will depend on the API provided by Jamf Pro.
    # For example, you might need to send a DELETE request to a specific URL.
    # You might also need to include some headers in the request.
    # Here's a basic example:
    print ("running... delete_profile_after_delay")
    token = generate_jamf_pro_token()
    url = app.config['JAMF_PRO_URL'] + '/JSSResource/osxconfigurationprofiles/id/' + profile_id
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

