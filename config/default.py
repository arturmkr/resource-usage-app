import os

APP_PORT = 10700
INIT_DB = False

DB_HOSTNAME = os.environ.get('DB_HOSTNAME', 'localhost')
DB_PORT = os.environ.get('DB_PORT', 5432)

DB_USERNAME = os.environ.get('DB_USERNAME', 'flask')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'flaskpassword')
DB_NAME = os.environ.get('DB_NAME', 'resource')
