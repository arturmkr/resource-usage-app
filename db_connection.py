from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Define the database connection details
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'flask'
DB_PASSWORD = 'flaskpassword'
DB_NAME = 'resource'

# Create the database URL for SQLAlchemy
db_url = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'

# Create the SQLAlchemy engine
engine = create_engine(db_url)

# Create a session factory
Session = sessionmaker(bind=engine)
