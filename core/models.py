 
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class InputType(Base):
    __tablename__ = 'input_type'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())

class Address(Base):
    __tablename__ = 'address'
    id = Column(Integer, primary_key=True)
    full_address = Column(Text, nullable=False)
    house_number = Column(String(50))
    created_at = Column(DateTime, default=func.now())

class InputRequest(Base):
    __tablename__ = 'input_request'
    id = Column(Integer, primary_key=True)
    input_type_id = Column(Integer, ForeignKey('input_type.id'))
    address_id = Column(Integer, ForeignKey('address.id'))
    attribute_name = Column(String(100))
    attribute_value = Column(Text)
    created_at = Column(DateTime, default=func.now())
