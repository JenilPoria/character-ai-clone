from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread" : False})

SessionLocal = sessionmaker(bind=engine,autoflush=False,autocommit = False)

Base = declarative_base()

def init_db():
    # Import models so they are registered with Base
    from app import models
    Base.metadata.create_all(bind = engine)
