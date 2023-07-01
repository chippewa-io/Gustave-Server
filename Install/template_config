class Config:
    """Base configuration."""
    MYSQL_DATABASE_HOST = ''  # change this line
    MYSQL_DATABASE_USER = ''
    MYSQL_DATABASE_PASSWORD = ''
    MYSQL_DATABASE_DB = ''
    MYSQL_DATABASE_PORT = 
    JAMF_PRO_URL = ''
    JAMF_PRO_USERNAME = ''
    JAMF_PRO_PASSWORD = ''
    CATEGORY_ID = 
    CATEGORY_NAME = ""
    PROFILE_DESCRIPTION = ""

class DevelopmentConfig(Config):
    USE_WAITRESS = False
    DEBUG = True
    TESTING = True
    TOKEN_EXPIRATION = 5 #in seconds.  31556926=year 2629743=month 86400=day 3600=hour

class TestingConfig(Config):
    USE_WAITRESS = False
    TESTING = True
    TOKEN_EXPIRATION = 2629743 #in seconds.  31556926=year 2629743=month 86400=day 3600=hour

class ProductionConfig(Config):
    USE_WAITRESS = True
    TOKEN_EXPIRATION = 2629743 #in seconds.  31556926=year 2629743=month 86400=day 3600=hour