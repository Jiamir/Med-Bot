from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db import crud
from ..db.models import Doctor
from typing import List, Optional

router = APIRouter()

# ----------------------------
# 1️⃣ Get all doctors
# ----------------------------
@router.get("/doctors", response_model=List[dict])
def get_all_doctors(db: Session = Depends(get_db)):
    doctors = db.query(Doctor).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "speciality": d.speciality,
            "location": d.location,
            "fee": d.fee,
            "keywords": d.keywords,
            "symptom_to_speciality": d.symptom_to_speciality,
            "disease_examples": d.disease_examples
        }
        for d in doctors
    ]

# ----------------------------
# 2️⃣ Search doctors by keyword or speciality
# ----------------------------
@router.get("/doctors/search", response_model=List[dict])
def search_doctors(
    keyword: Optional[str] = Query(None, description="Keyword to search doctors"),
    speciality: Optional[str] = Query(None, description="Filter by speciality"),
    db: Session = Depends(get_db)
):
    query = db.query(Doctor)
    
    if keyword:
        query = query.filter(Doctor.keywords.ilike(f"%{keyword}%"))
    if speciality:
        query = query.filter(Doctor.speciality.ilike(f"%{speciality}%"))
    
    results = query.all()
    
    return [
        {
            "id": d.id,
            "name": d.name,
            "speciality": d.speciality,
            "location": d.location,
            "fee": d.fee,
            "keywords": d.keywords,
            "symptom_to_speciality": d.symptom_to_speciality,
            "disease_examples": d.disease_examples
        }
        for d in results
    ]
