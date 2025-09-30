from langchain.vectorstores import FAISS
from langchain.schema import Document
from sqlalchemy.orm import Session
from sqlalchemy import or_
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

from app.db.models import Doctor, DocumentModel
from app.core.embeddings import embeddings

# ----------------------------
# Config
# ----------------------------
FAISS_INDEX_PATH = "faiss_index"
vectorstore: FAISS = None

# ----------------------------
# 1️⃣ Build FAISS vectorstore
# ----------------------------
def build_vectorstore(db: Session, persist: bool = True):
    global vectorstore

    if embeddings is None:
        print("❌ Embeddings not available, skipping vectorstore build")
        return None

    # Try to load existing
    if persist and os.path.exists(FAISS_INDEX_PATH):
        try:
            # ✅ Try with the parameter first (newer versions)
            try:
                vectorstore = FAISS.load_local(
                    FAISS_INDEX_PATH,
                    embeddings,
                    allow_dangerous_deserialization=True
                )
            except TypeError:
                # ✅ Fallback for older versions without the parameter
                vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings)
            
            print("✅ Loaded existing FAISS vectorstore")
            return vectorstore
        except Exception as e:
            print(f"⚠️ Could not load existing vectorstore: {e}")
            print("🔄 Building new vectorstore...")

    try:
        # Doctors
        doctors = db.query(Doctor).all()
        print(f"📋 Processing {len(doctors)} doctors...")

        doctor_docs = [
            Document(
                page_content=f"Doctor {d.name}. Speciality: {d.speciality or ''}. "
                             f"Keywords: {d.keywords or ''}. "
                             f"Symptoms: {d.symptom_to_speciality or ''}. "
                             f"Diseases: {d.disease_examples or ''}. "
                             f"Location: {d.location or ''}",
                metadata={
                    "id": d.id,
                    "type": "doctor",
                    "name": d.name,
                    "speciality": d.speciality,
                    "location": d.location,
                    "fee": getattr(d, 'fee', None)
                }
            )
            for d in doctors
        ]

        # Documents (resources)
        documents = db.query(DocumentModel).all()
        print(f"📚 Processing {len(documents)} documents...")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " "]
        )

        document_docs = []
        for r in documents:
            chunks = text_splitter.split_text(r.content or "")
            for i, chunk in enumerate(chunks):
                document_docs.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "id": r.id,
                            "type": "resource",
                            "title": r.title,
                            "url": r.url
                        }
                    )
                )

        # Combine
        all_docs = doctor_docs + document_docs
        print(f"🔨 Building FAISS index with {len(all_docs)} total documents...")
        vectorstore = FAISS.from_documents(all_docs, embeddings)
        print("✅ Built new FAISS vectorstore")

        if persist:
            vectorstore.save_local(FAISS_INDEX_PATH)
            print("💾 Saved vectorstore to disk")

        return vectorstore

    except Exception as e:
        print(f"❌ Error building vectorstore: {e}")
        import traceback
        traceback.print_exc()
        vectorstore = None
        return None


# ----------------------------
# 2️⃣ Doctor retrieval
# ----------------------------
def retrieve_doctors(query: str, k: int = 5):
    if vectorstore is None:
        print("⚠️ Vectorstore not available")
        return []

    try:
        results = vectorstore.similarity_search(query, k=k)
        doctors = [r.metadata for r in results if r.metadata.get("type") == "doctor"]
        return doctors
    except Exception as e:
        print(f"❌ Error in doctor search: {e}")
        return []


# ----------------------------
# 3️⃣ Resource retrieval
# ----------------------------
def retrieve_resources(query: str, top_k: int = 5):  # ✅ Fixed parameter name
    if vectorstore is None:
        print("⚠️ Vectorstore not available")
        return []

    try:
        results = vectorstore.similarity_search(query, k=top_k)
        resources = [r.metadata for r in results if r.metadata.get("type") == "resource"]
        return resources
    except Exception as e:
        print(f"❌ Error in resource search: {e}")
        return []


# ----------------------------
# 4️⃣ Mixed retrieval (doctors + resources)
# ----------------------------
def retrieve_mixed(query: str, k: int = 10):
    if vectorstore is None:
        print("⚠️ Vectorstore not available")
        return {"doctors": [], "resources": []}

    try:
        results = vectorstore.similarity_search(query, k=k)
        doctors, resources = [], []

        for r in results:
            if r.metadata.get("type") == "doctor":
                doctors.append(r.metadata)
            elif r.metadata.get("type") == "resource":
                resources.append(r.metadata)

        return {"doctors": doctors, "resources": resources}
    except Exception as e:
        print(f"❌ Mixed retrieval failed: {e}")
        return {"doctors": [], "resources": []}


# ----------------------------
# 5️⃣ Doctor retrieval pipeline (semantic + fallback keyword)
# ----------------------------
def retrieve_top_doctors(query: str, db: Session, top_k: int = 5):
    global vectorstore

    if vectorstore is None and embeddings is not None:
        print("⚠️ Vectorstore not initialized, building now...")
        build_vectorstore(db)

    if vectorstore is not None:
        try:
            import time
            start = time.time()
            
            # ✅ Search with timeout protection
            top_metadata = vectorstore.similarity_search(query, k=top_k * 2)  # Get more to filter
            
            elapsed = time.time() - start
            print(f"⏱️ FAISS search took {elapsed:.2f}s")
            
            if top_metadata:
                top_ids = [
                    m.metadata.get("id")
                    for m in top_metadata if m.metadata.get("type") == "doctor"
                ][:top_k]  # Limit after filtering
                
                top_ids = [i for i in top_ids if i is not None]

                from app.db import crud
                doctors = crud.get_doctors_by_ids(db, top_ids) if top_ids else []
                if doctors:
                    print(f"✅ Found {len(doctors)} doctors via semantic search")
                    return doctors
        except Exception as e:
            print(f"⚠️ Semantic search failed: {e}")
            import traceback
            traceback.print_exc()

    print("🔎 Falling back to keyword search")
    return keyword_search_doctors(query, db, top_k)


# ----------------------------
# 6️⃣ Keyword search fallback
# ----------------------------
def keyword_search_doctors(query: str, db: Session, limit: int = 5):
    try:
        query_lower = query.lower().strip()
        print(f"🔎 Keyword searching for: '{query_lower}'")

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
            'autism': 'pediatrics',  # ✅ Added autism mapping
            'general': 'general medicine'
        }

        specialty_queries = [s for k, s in specialty_mapping.items() if k in query_lower]
        doctors_query = db.query(Doctor)

        if specialty_queries:
            doctors_query = doctors_query.filter(
                or_(*[Doctor.speciality.ilike(f"%{s}%") for s in specialty_queries])
            )
        else:
            doctors_query = doctors_query.filter(
                or_(
                    Doctor.name.ilike(f"%{query_lower}%"),
                    Doctor.speciality.ilike(f"%{query_lower}%"),
                    (Doctor.keywords != None) & Doctor.keywords.ilike(f"%{query_lower}%"),
                    Doctor.location.ilike(f"%{query_lower}%")
                )
            )

        doctors = doctors_query.limit(limit).all()
        print(f"✅ Keyword search found {len(doctors)} doctors")
        return doctors

    except Exception as e:
        print(f"❌ Keyword search error: {e}")
        return []