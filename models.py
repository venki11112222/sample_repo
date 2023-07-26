from sqlalchemy import Column, Integer, String
from database import Base

class Boss(Base):
    __tablename__ = "boss"
    id = Column(Integer, primary_key=True)
    name=Column(String, unique=True,index=True)
    email = Column(String, unique=True,index=True)
    password=Column(String, unique=True,index=True)
