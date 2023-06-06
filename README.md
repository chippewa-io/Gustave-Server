# Gustave


Gustave is a Flask application designed to manage and secure communication between client computers and a Jamf Pro server.

## Overview

The application works as follows:

1. The client computer requests a secret from Gustave by providing its UDID.
2. Gustave uses this UDID to search for an enrolled computer record in Jamf Pro.
3. Jamf Pro returns the Computer ID to Gustave.
4. Gustave stores the UDID, Computer ID, a generated secret, and a future timestamp in MySQL.
5. Gustave tells Jamf Pro to create and scope a configuration profile to the computer.
6. Jamf Pro sends a payload containing the secret to the client.
7. The client receives the payload with the secret.
8. The client uses the secret to authenticate to the /computers endpoint on Gustave.
9. Gustave checks MySQL for a matching UDID, secret, and unexpired timestamp.
10. If all three are found, Gustave retrieves the computer record from Jamf Pro and provides it to the client.

## Installation

1. Clone the repository: `git clone https://github.com/username/gustave.git`
2. Navigate to the project directory: `cd gustave`
3. Install the requirements: `pip install -r requirements.txt`
4. Set up your MySQL database and update the `config.py` file with your database credentials and other configuration settings.
5. Run the application: `python app.py`
