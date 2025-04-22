from sqlalchemy import Column, Integer, String, VARBINARY
from database import Base

class User(Base):
    __tablename__ = 'users'  # Double underscores for __tablename__

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(30), unique=True, nullable=False)  # Add nullable=False for required fields
    password = Column(VARBINARY(32), nullable=False)  # Use LargeBinary for binary data
    salt = Column(VARBINARY(32), nullable=False)  # Use LargeBinary for binary data

    
class File(Base):
    __tablename__ = 'files'
    
    user_id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(30), index=True)
    key = Column(VARBINARY(16), nullable=False)
    backup_key = Column(VARBINARY(16), nullable=True)
