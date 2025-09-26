from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from sqlalchemy.orm import Session
from app.db.models import Doctor
from app.core.embeddings import embeddings
import os
from sqlalchemy import or_

# Path to persist FAISS index
FAISS_INDEX_PATH = "faiss_index"

# In-memory vectorstore
vectorstore: FAISS = None

# ----------------------------
# 1️⃣ Build FAISS vectorstore
# ----------------------------
def build_vectorstore(db: Session, persist: bool = True):
    global vectorstore

    if embeddings is None:
        print("❌ Embeddings not available, skipping vectorstore build")
        return None

    # Load from disk if available
    if persist and os.path.exists(FAISS_INDEX_PATH):
        try:
            vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
            print("✅ Loaded existing FAISS vectorstore")
            return vectorstore
        except Exception as e:
            print(f"⚠️ Could not load existing vectorstore: {e}")

    try:
        doctors = db.query(Doctor).all()
        print(f"📋 Found {len(doctors)} doctors in database")

        if not doctors:
            print("⚠️ No doctors found in database")
            return None

        docs = [
            Document(
                page_content=f"Speciality: {d.speciality or ''}. "
                             f"Keywords: {d.keywords or ''}. "
                             f"Symptoms: {d.symptom_to_speciality or ''}. "
                             f"Diseases: {d.disease_examples or ''}. "
                             f"Location: {d.location or ''}",
                metadata={
                    "id": d.id,
                    "name": d.name,
                    "speciality": d.speciality,
                    "location": d.location,
                    "fee": getattr(d, 'fee', None)
                }
            )
            for d in doctors
        ]

        vectorstore = FAISS.from_documents(docs, embeddings)
        print("✅ Built new FAISS vectorstore")

        if persist:
            vectorstore.save_local(FAISS_INDEX_PATH)
            print("💾 Saved vectorstore to disk")

        return vectorstore

    except Exception as e:
        print(f"❌ Error building vectorstore: {e}")
        vectorstore = None
        return None


# ----------------------------
# 2️⃣ Semantic search
# ----------------------------
def retrieve_doctors(query: str, k: int = 5):
    if vectorstore is None:
        print("⚠️ Vectorstore not available")
        return []

    try:
        results = vectorstore.similarity_search(query, k=k)
        return [r.metadata for r in results]
    except Exception as e:
        print(f"❌ Error in semantic search: {e}")
        return []


# ----------------------------
# 3️⃣ Retrieval pipeline
# ----------------------------
def retrieve_top_doctors(query: str, db: Session, top_k: int = 5):
    global vectorstore

    if vectorstore is None and embeddings is not None:
        build_vectorstore(db)

    if vectorstore is not None:
        try:
            top_metadata = vectorstore.similarity_search(query, k=top_k)
            if top_metadata:
                top_ids = [m.metadata["id"] for m in top_metadata]
                from ..db import crud
                doctors = crud.get_doctors_by_ids(db, top_ids) if top_ids else []
                if doctors:
                    print(f"✅ Found {len(doctors)} doctors via semantic search")
                    return doctors
        except Exception as e:
            print(f"⚠️ Semantic search failed: {e}")

    print("🔎 Falling back to keyword search")
    return keyword_search_doctors(query, db, top_k)


# ----------------------------
# 4️⃣ Keyword search fallback
# ----------------------------
def keyword_search_doctors(query: str, db: Session, limit: int = 5):
    try:
        query_lower = query.lower().strip()
        print(f"🔎 Searching for: '{query_lower}'")

        # Basic specialty mapping
        specialty_mapping = {
            'heart': 'cardiology',
            'cardio': 'cardiology',
            'gynae': 'gynecology',
            'skin': 'dermatology',
            'bone': 'orthopedics',
            'eye': 'ophthalmology',
            'brain': 'neurology',
            'child': 'pediatrics',
            'general': 'general medicine'
        }

        # Match specialty keywords
        specialty_queries = [s for k, s in specialty_mapping.items() if k in query_lower]

        doctors_query = db.query(Doctor)

        if specialty_queries:
            doctors_query = doctors_query.filter(
                or_(*[Doctor.speciality.ilike(f"%{s}%") for s in specialty_queries])
            )

        # Fallback: general keyword search
        if not specialty_queries:
            doctors_query = doctors_query.filter(
                or_(
                    Doctor.name.ilike(f"%{query_lower}%"),
                    Doctor.speciality.ilike(f"%{query_lower}%"),
                    Doctor.keywords.ilike(f"%{query_lower}%"),
                    Doctor.location.ilike(f"%{query_lower}%")
                )
            )

        doctors = doctors_query.limit(limit).all()
        print(f"✅ Keyword search found {len(doctors)} doctors")
        return doctors

    except Exception as e:
        print(f"❌ Keyword search error: {e}")
        return []
