import sys
import os
import importlib.util
from flask import Flask
from waitress import serve
import logging

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append('/etc/gustave')

# Load config
spec = importlib.util.spec_from_file_location('config', '/etc/gustave/config.py')
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
logging.basicConfig(level=logging.INFO)


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

    if app.config['USE_WAITRESS']:
        serve(app, host='127.0.0.1', port=8000)
    else:
        app.run(host='127.0.0.1', port=8000, debug=True)
