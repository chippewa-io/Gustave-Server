class Config:
    """Base configuration."""
    DEBUG = True
    TESTING = True
    TOKEN_EXPIRATION = 90
    MYSQL_DATABASE_HOST = '127.0.0.1'  # change this line
    MYSQL_DATABASE_USER = 'chris'
    MYSQL_DATABASE_PASSWORD = 'gustave2'
    MYSQL_DATABASE_DB = 'secrets'
    MYSQL_DATABASE_PORT = 3306
    JAMF_PRO_URL = 'https://tcohoon.jamfcloud.com'
    JAMF_PRO_USERNAME = 'admin'
    JAMF_PRO_PASSWORD = 'jamf1234'
    CATEGORY_ID = 4
    CATEGORY_NAME = "Gustave Tokens"
    PROFILE_DESCRIPTION = "This profile is used on the backend of your system.  Please ignore this."

class DevelopmentConfig(Config):
    CONFIG_CLASS = 'config.DevelopmentConfig'

class ProductionConfig(Config):
    pass

class TestingConfig(Config):
    pass
