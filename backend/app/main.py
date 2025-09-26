from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.api.chat import router as chat_router
from app.db.database import SessionLocal
from app.api import rag

app = FastAPI(title="Med-Bot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")

# ----------------------------
# Build/load FAISS vectorstore on startup (with error handling)
# ----------------------------
@app.on_event("startup")
def startup_event():
    print("Starting up: building/loading FAISS vectorstore...")
    db: Session = SessionLocal()
    try:
        vectorstore = rag.build_vectorstore(db)
        if vectorstore:
            print("Vectorstore ready!")
        else:
            print("Vectorstore not available, using keyword search fallback")
    except Exception as e:
        print(f"Error building vectorstore: {e}")
        print("App will continue with keyword search fallback")
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Med-Bot API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}