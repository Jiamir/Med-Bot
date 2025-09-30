from langchain.vectorstores import FAISS
from langchain.schema import Document
from sqlalchemy.orm import Session
from sqlalchemy import or_
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

from app.db.models import Therapist, DocumentModel
from app.core.embeddings import embeddings

# ----------------------------
# Config
# ----------------------------
FAISS_INDEX_PATH = "faiss_index_therapists"
vectorstore: FAISS = None

# ----------------------------
# 1️⃣ Build FAISS vectorstore
# ----------------------------
def build_vectorstore(db: Session, persist: bool = True):
    global vectorstore

    if embeddings is None:
        print("❌ Embeddings not available, skipping vectorstore build")
        return None

    if persist and os.path.exists(FAISS_INDEX_PATH):
        try:
            try:
                vectorstore = FAISS.load_local(
                    FAISS_INDEX_PATH,
                    embeddings,
                    allow_dangerous_deserialization=True
                )
            except TypeError:
                vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings)
            print("✅ Loaded existing FAISS vectorstore")
            return vectorstore
        except Exception as e:
            print(f"⚠️ Could not load existing vectorstore: {e}")
            print("🔄 Building new vectorstore...")

    try:
        therapists = db.query(Therapist).all()
        print(f"📋 Processing {len(therapists)} therapists...")

        therapist_docs = [
            Document(
                page_content=f"Therapist {t.provider_name}. Company: {t.company_name or ''}. "
                             f"Type: {t.provider_type or ''}. "
                             f"Keywords: {t.keywords or ''}. "
                             f"Description: {t.description or ''}. "
                             f"Location: {t.address or ''}, {t.city or ''}, {t.state or ''}",
                metadata={
                    "id": t.id,
                    "type": "therapist",
                    "provider_name": t.provider_name,
                    "company_name": t.company_name,
                    "provider_type": t.provider_type,
                    "email": t.email,
                    "location": t.address
                }
            )
            for t in therapists
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

        # Combine all
        all_docs = therapist_docs + document_docs
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
# 2️⃣ Therapist retrieval
# ----------------------------
def retrieve_therapists(query: str, k: int = 5):
    if vectorstore is None:
        print("⚠️ Vectorstore not available")
        return []

    try:
        results = vectorstore.similarity_search(query, k=k)
        therapists = [r.metadata for r in results if r.metadata.get("type") == "therapist"]
        return therapists
    except Exception as e:
        print(f"❌ Error in therapist search: {e}")
        return []

# ----------------------------
# 3️⃣ Resource retrieval
# ----------------------------
def retrieve_resources(query: str, top_k: int = 5):
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
# 4️⃣ Mixed retrieval (therapists + resources)
# ----------------------------
def retrieve_mixed(query: str, k: int = 10):
    if vectorstore is None:
        print("⚠️ Vectorstore not available")
        return {"therapists": [], "resources": []}

    try:
        results = vectorstore.similarity_search(query, k=k)
        therapists, resources = [], []

        for r in results:
            if r.metadata.get("type") == "therapist":
                therapists.append(r.metadata)
            elif r.metadata.get("type") == "resource":
                resources.append(r.metadata)

        return {"therapists": therapists, "resources": resources}
    except Exception as e:
        print(f"❌ Mixed retrieval failed: {e}")
        return {"therapists": [], "resources": []}

# ----------------------------
# 5️⃣ Therapist retrieval pipeline (semantic + fallback keyword)
# ----------------------------
def retrieve_top_therapists(query: str, db: Session, top_k: int = 5):
    global vectorstore

    if vectorstore is None and embeddings is not None:
        print("⚠️ Vectorstore not initialized, building now...")
        build_vectorstore(db)

    if vectorstore is not None:
        try:
            import time
            start = time.time()
            
            top_metadata = vectorstore.similarity_search(query, k=top_k * 2)
            elapsed = time.time() - start
            print(f"⏱️ FAISS search took {elapsed:.2f}s")
            
            if top_metadata:
                top_ids = [
                    m.metadata.get("id")
                    for m in top_metadata if m.metadata.get("type") == "therapist"
                ][:top_k]
                top_ids = [i for i in top_ids if i is not None]

                from app.db import crud
                therapists = crud.get_therapists_by_ids(db, top_ids) if top_ids else []
                if therapists:
                    print(f"✅ Found {len(therapists)} therapists via semantic search")
                    return therapists
        except Exception as e:
            print(f"⚠️ Semantic search failed: {e}")
            import traceback
            traceback.print_exc()

    print("🔎 Falling back to keyword search")
    return keyword_search_therapists(query, db, top_k)

# ----------------------------
# 6️⃣ Keyword search fallback for therapists
# ----------------------------
def keyword_search_therapists(query: str, db: Session, limit: int = 5):
    try:
        query_lower = query.lower().strip()
        from app.db import crud

        therapists_query = db.query(Therapist).filter(
            or_(
                Therapist.provider_name.ilike(f"%{query_lower}%"),
                (Therapist.keywords != None) & Therapist.keywords.ilike(f"%{query_lower}%"),
                Therapist.provider_type.ilike(f"%{query_lower}%"),
                Therapist.city.ilike(f"%{query_lower}%"),
                Therapist.state.ilike(f"%{query_lower}%")
            )
        )

        therapists = therapists_query.limit(limit).all()
        print(f"✅ Keyword search found {len(therapists)} therapists")
        return therapists

    except Exception as e:
        print(f"❌ Keyword search error: {e}")
        return []
