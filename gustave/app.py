# app.py
import sys
import os
import importlib.util

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from flask import Flask
from flask_apscheduler import APScheduler
from waitress import serve
import logging

# Import blueprints
from routes.computers import computers_bp
from routes.token_generation import token_generation_bp
from routes.secret import secrets_bp
from routes.profiles import profiles_bp

# Import init_db function
from services import init_db, cleanup_expired_profiles

# Load config
spec = importlib.util.spec_from_file_location('config', '/etc/gustave/config.py')
Config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Config)

# Create app
def create_app(config_class='DevelopmentConfig'):
    app = Flask(__name__)
    # Configure the app with the given config class (defaulting to DevelopmentConfig)
    app.config.from_object(getattr(Config, config_class))
    # Initialize MySQL extension
    init_db(app)
    
    # Initialize APScheduler
    #scheduler = APScheduler()
    #scheduler.init_app(app)
    
    # Add a job that runs every X minutes
    #if not scheduler.running:
    #    scheduler.add_job(func=cleanup_expired_profiles, trigger='interval', minutes=1, id='cleanup_expired_profiles', args=(app,))
    #    scheduler.start()
    #    app.logger.info("Scheduler started")
    #else:
    #    app.logger.info("Scheduler already running")
    
    # Register the blueprints
    app.register_blueprint(computers_bp, url_prefix='/api')
    app.register_blueprint(token_generation_bp, url_prefix='/api')
    app.register_blueprint(secrets_bp, url_prefix='/api')
    app.register_blueprint(profiles_bp, url_prefix='/api')
    return app

if __name__ == '__main__':
    config_class = os.getenv('FLASK_CONFIG', 'DevelopmentConfig')
    app = create_app(config_class=config_class)

    if getattr(Config, config_class).USE_WAITRESS:
        serve(app, host='127.0.0.1', port=8000)
    else:
        app.run(host='127.0.0.1', port=8000, debug=True)
