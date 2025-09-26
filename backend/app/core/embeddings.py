from langchain_huggingface import HuggingFaceEmbeddings

# Initialize HuggingFace embeddings
try:
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    print("✅ HuggingFace embeddings loaded successfully")
except Exception as e:
    print(f"❌ Error loading HuggingFace embeddings: {e}")
    embeddings = None
