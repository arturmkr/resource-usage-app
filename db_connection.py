from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.default import DB_USERNAME, DB_PASSWORD, DB_HOSTNAME, DB_PORT, DB_NAME

# Create the database URL for SQLAlchemy
db_url = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}"

# Create the SQLAlchemy engine
engine = create_engine(db_url)

# Create a session factory
Session = sessionmaker(bind=engine)
