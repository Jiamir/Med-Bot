from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric
from .database import Base
from sqlalchemy.types import UserDefinedType

# ✅ Define VECTOR manually for pgvector extension
class VECTOR(UserDefinedType):
    def __init__(self, dim: int):
        self.dim = dim

    def get_col_spec(self):
        return f"vector({self.dim})"

# ----------------------------
# Doctor Model
# ----------------------------
class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    designation = Column(String)
    speciality = Column(String, nullable=False)
    location = Column(String)
    fee = Column(Integer)
    keywords = Column(Text)  # comma-separated for search
    symptom_to_speciality = Column(Text)
    disease_examples = Column(Text)

# ----------------------------
# Document Model
# ----------------------------
class DocumentModel(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String)
    title = Column(String)
    url = Column(String)
    content = Column(Text)

# ----------------------------
# Therapist Model
# ----------------------------
class Therapist(Base):
    __tablename__ = "therapists"
    id = Column(Integer, primary_key=True, index=True)
    therapist_id = Column(String, unique=True)
    company_name = Column(Text)
    provider_name = Column(Text, nullable=False)
    provider_type = Column(Text)
    email = Column(Text)
    public_phone = Column(Text)
    gender = Column(Text)
    website_url = Column(Text)
    description = Column(Text)
    spanish_description = Column(Text)
    keywords = Column(Text)
    image_url = Column(Text)
    image_url_sas = Column(Text)
    address = Column(Text)
    state = Column(Text)
    city = Column(Text)
    zip_code = Column(Text)
    county = Column(Text)
    list_address = Column(Boolean)
    latitude = Column(Numeric(10,7))
    longitude = Column(Numeric(10,7))
    by_appointment = Column(Boolean)
    walkin = Column(Boolean)
    allow_virtual = Column(Boolean)
    accessible_by_bus = Column(Boolean)
    accessible_by_train = Column(Boolean)
    accessible_for_disabled = Column(Boolean)
    embedding = Column(VECTOR(384))  # ✅ Now works with PostgreSQL + pgvector
