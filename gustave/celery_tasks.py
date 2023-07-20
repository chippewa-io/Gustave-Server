import requests
import logging
from celery import Celery
from services import generate_jamf_pro_token

# Create a Celery instance
celery = Celery(__name__)

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

