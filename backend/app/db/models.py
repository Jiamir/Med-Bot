from sqlalchemy import Column, Integer, String, Text
from .database import Base

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    designation = Column(String)
    speciality = Column(String, nullable=False)
    location = Column(String)
    fee = Column(Integer)
    keywords = Column(Text)  # comma-separated for search
    symptom_to_speciality = Column(Text)  # added
    disease_examples = Column(Text)        # added
