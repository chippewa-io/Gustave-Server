class Config:
    """Base configuration."""
    MYSQL_DATABASE_HOST = '127.0.0.1'  # change this line
    MYSQL_DATABASE_USER = 'beaver'
    MYSQL_DATABASE_PASSWORD = 'gustave03'
    MYSQL_DATABASE_DB = 'secrets'
    MYSQL_DATABASE_PORT = 3306
    JAMF_PRO_URL = 'https://tcohoon.jamfcloud.com'
    JAMF_PRO_USERNAME = 'admin'
    JAMF_PRO_PASSWORD = 'jamf1234'
    CATEGORY_ID = 5
    CATEGORY_NAME = "Gustave Tokens"
    PROFILE_DESCRIPTION = "This profile is used on the backend of your system.  Please ignore this."

class DevelopmentConfig(Config):
    CONFIG_CLASS = 'config.DevelopmentConfig'
    USE_WAITRESS = False
    DEBUG = True
    TESTING = True
    TOKEN_EXPIRATION = 5 #in seconds.  31556926=year 2629743=month 86400=day 3600=hour

class TestingConfig(Config):
    CONFIG_CLASS = 'config.TestingConfig'
    USE_WAITRESS = False
    TESTING = True
    TOKEN_EXPIRATION = 2629743 #in seconds.  31556926=year 2629743=month 86400=day 3600=hour

class ProductionConfig(Config):
    CONFIG_CLASS = 'config.ProductionConfig'
    USE_WAITRESS = True
    TOKEN_EXPIRATION = 2629743 #in seconds.  31556926=year 2629743=month 86400=day 3600=hour