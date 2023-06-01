# app.py
from flask import Flask
import config
from flask_apscheduler import APScheduler
# Import blueprints
from routes.computers import computers_bp
from routes.token_generation import token_generation_bp
from routes.secret import secrets_bp
# Import init_db function
from services import init_db, insert_into_active_profiles

# Create app
def create_app(config_class=config.DevelopmentConfig):
    app = Flask(__name__)
    # Configure the app with the given config class (defaulting to DevelopmentConfig)
    app.config.from_object(config_class)
    # Initialize MySQL extension
    init_db(app)
    # Initialize APScheduler
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    # Add a job that runs every 10 seconds
    scheduler.add_job('insert_into_active_profiles', trigger='interval', seconds=10, id='my_job')
    # Register the blueprints
    app.register_blueprint(computers_bp, url_prefix='/api')
    app.register_blueprint(token_generation_bp, url_prefix='/api')
    app.register_blueprint(secrets_bp, url_prefix='/api')
    #app.register_blueprint(computer_bp, url_prefix='/api')
    return app

if __name__ == '__main__':
    app = create_app(config_class=config.DevelopmentConfig)
    app.run(debug=True)
