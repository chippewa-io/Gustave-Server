# app.py
import sys
import os
import importlib.util

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append('/etc/gustave')

from flask import Flask
from waitress import serve
import logging

# Import blueprints
from routes.computers import computers_bp
from routes.token_generation import token_generation_bp
from routes.secret import secrets_bp
from routes.profiles import profiles_bp

# Import init_db function
from services import init_db

# Load config
spec = importlib.util.spec_from_file_location('config', '/etc/gustave/config.py')
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

# Determine which config to use based on environment variable
config_name = os.getenv('FLASK_CONFIG', 'development')

if config_name == 'development':
    Config = config_module.DevelopmentConfig
elif config_name == 'testing':
    Config = config_module.TestingConfig
elif config_name == 'production':
    Config = config_module.ProductionConfig
else:
    Config = config_module.DevelopmentConfig  # default to DevelopmentConfig if no match

##loging
logging.basicConfig(level=logging.INFO)


# Create app
def create_app(config_class=Config):
    app = Flask(__name__)
    # Configure the app with the given config class (defaulting to DevelopmentConfig)
    #app.config.from_object(getattr(Config, config_class))
    app.config.from_object(config_class)
    # Initialize MySQL extension
    init_db(app)
    
    # Register the blueprints
    app.register_blueprint(computers_bp, url_prefix='/api')
    app.register_blueprint(token_generation_bp, url_prefix='/api')
    app.register_blueprint(secrets_bp, url_prefix='/api')
    app.register_blueprint(profiles_bp, url_prefix='/api')
    return app

if __name__ == '__main__':
    config_class = os.getenv('FLASK_CONFIG', 'DevelopmentConfig')
    app = create_app(config_class='config.' + config_class)

    if getattr(config_module, config_class).USE_WAITRESS:
        serve(app, host='127.0.0.1', port=8000)
    else:
        app.run(host='127.0.0.1', port=8000, debug=True)