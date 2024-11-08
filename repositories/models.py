from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    JSON,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Numeric,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# tabla para almacenar la certeza o calidad de las APIs de geolocalización
class AddressScore(Base):
    __tablename__ = "address_score"
    id = Column(Integer, primary_key=True)
    address_id = Column(Integer, ForeignKey("address.id"))
    quality_label = Column(String(50), default="calidad origen dato")
    score = Column(String(20))


# tabla para guardar el request y response de cada API de geolocalización
class ApiResponse(Base):
    __tablename__ = "api_response"
    id = Column(Integer, primary_key=True)
    type_api_id = Column(Integer, ForeignKey("type_api_geocord.id", ondelete="CASCADE"))
    address_id = Column(Integer, ForeignKey("address.id"))
    attribute_name = Column(String(100))
    attribute_value = Column(Text)
    created_at = Column(DateTime, default=func.now())


# tabla para registrar logs de entrada y salida de las APIs de geolocalización
class ApiLogs(Base):
    __tablename__ = "api_logs"
    id = Column(Integer, primary_key=True)
    api_response_id = Column(Integer, ForeignKey("api_response.id", ondelete="CASCADE"))
    address_id = Column(Integer, ForeignKey("address.id", ondelete="CASCADE"))
    request_payload = Column(JSON)  # Guardar la solicitud como JSON
    response_payload = Column(JSON)  # Guardar la respuesta como JSON
    created_at = Column(DateTime, default=func.now())
    status_code = Column(Integer)
    response_time_ms = Column(Integer)


class InputType(Base):
    __tablename__ = "input_type"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())


class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    full_address = Column(Text, nullable=False)
    normalized_address = Column(Text)
    input_type_id = Column(Integer, ForeignKey("input_type.id"))
    created_at = Column(DateTime, default=func.now())
    ip_address = Column(INET)
    house_number = Column(String(50))
    street = Column(String(100))
    neighbourhood = Column(String(100))
    sector = Column(String(100))
    commune = Column(String(100))
    city = Column(String(100))
    province = Column(String(100))
    region = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="Chile")
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    last_update = Column(DateTime)


class InputRequest(Base):
    __tablename__ = "input_request"
    id = Column(Integer, primary_key=True)
    input_type_id = Column(Integer, ForeignKey("input_type.id"))
    address_id = Column(Integer, ForeignKey("address.id"))
    attribute_name = Column(String(100))
    attribute_value = Column(Text)
    created_at = Column(DateTime, default=func.now())
