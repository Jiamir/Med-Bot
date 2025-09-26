from sqlalchemy.orm import Session
from .models import Doctor

def get_doctors_by_keyword(db: Session, keyword: str):
    return db.query(Doctor).filter(Doctor.keywords.ilike(f"%{keyword}%")).all()

def get_doctor_by_id(db: Session, doctor_id: int):
    return db.query(Doctor).filter(Doctor.id == doctor_id).first()

def get_doctors_by_ids(db: Session, ids: list):
    return db.query(Doctor).filter(Doctor.id.in_(ids)).all()
