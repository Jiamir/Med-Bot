from sqlalchemy.orm import Session
from .models import Doctor, DocumentModel, Therapist

def get_doctors_by_keyword(db: Session, keyword: str):
    return db.query(Doctor).filter(Doctor.keywords.ilike(f"%{keyword}%")).all()

def get_doctor_by_id(db: Session, doctor_id: int):
    return db.query(Doctor).filter(Doctor.id == doctor_id).first()

def get_doctors_by_ids(db: Session, ids: list):
    return db.query(Doctor).filter(Doctor.id.in_(ids)).all()

def get_all_documents(db: Session):
    return db.query(DocumentModel).all()

def get_document_by_id(db: Session, document_id: int):
    return db.query(DocumentModel).filter(DocumentModel.id == document_id).first()

def get_therapists_by_keyword(db: Session, keyword: str):
    return db.query(Therapist).filter(Therapist.keywords.ilike(f"%{keyword}%")).all()

def get_therapist_by_id(db: Session, therapist_id: int):
    return db.query(Therapist).filter(Therapist.id == therapist_id).first()

def get_therapists_by_ids(db: Session, ids: list):
    return db.query(Therapist).filter(Therapist.id.in_(ids)).all()
