import sys
import os
import signal
import importlib.util
from flask import Flask
from waitress import serve
import logging
import logging.handlers
import threading
from threading import Thread
from threading import Event

###############################################
#setup event to signal license invalid
license_invalid_event = Event()

###############################################
# Add the parent directory to the path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append('/etc/gustave')

###############################################
# Load config
spec = importlib.util.spec_from_file_location('config', '/etc/gustave/config.py')
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

###############################################
# Set up logging
log_size = 10 * 1024 * 1024  # 10 MB
handler = logging.handlers.RotatingFileHandler('/var/log/gustave.log', maxBytes=log_size, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])

###############################################
def create_app(config_name=None):
    app = Flask(__name__)

    # Determine configuration based on environment variable or passed argument
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    if config_name == 'development':
        Config = config_module.DevelopmentConfig
    elif config_name == 'testing':
        Config = config_module.TestingConfig
    elif config_name == 'production':
        Config = config_module.ProductionConfig
    else:
        Config = config_module.DevelopmentConfig

    # Apply configuration
    app.config.from_object(Config)

    # Initialize services & extensions
    from services import init_db
    init_db(app)

    # Initialize the cleaner
    from cleaner import run_cleaner

    # Initialize chequamegon
    from chequamegon import run_activation_check



    # Register blueprints
    from routes.computers import computers_bp
    from routes.secret import secrets_bp
    from routes.profiles import profiles_bp

    app.register_blueprint(computers_bp, url_prefix='/api')
    app.register_blueprint(secrets_bp, url_prefix='/api')
    app.register_blueprint(profiles_bp, url_prefix='/api')

    return app

if __name__ == '__main__':
    app = create_app()

    # Start the activation check in a separate thread
    activation_thread = Thread(target=run_activation_check)
    activation_thread.start()

    # Start the profile cleanup in a separate thread
    cleaner_thread = Thread(target=run_cleaner)
    cleaner_thread.start()


    if app.config['USE_WAITRESS']:
        serve(app, host='127.0.0.1', port=8000)
        # Poll the event, check every week
        while not license_invalid_event.is_set():
            time.sleep(604800)  # Check again in a week
            os.kill(os.getpid(), signal.SIGINT)
    else:
        app.run(host='127.0.0.1', port=8000, debug=True)
