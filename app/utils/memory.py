import  chromadb 
from chromadb.utils import embedding_functions
import uuid

# --- CONFIGURATION ---
# We use a lightweight, high-speed model for embeddings.
# This runs LOCALLY on your machine (Free & Private).
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Initialize ChromaDB Client (Persistent = Saves to disk)
chroma_client = chromadb.PersistentClient(path="./chroma_db")

print("⏳ Downloading AI Model (approx 80MB)...")
# Setup the Embedding Function (The "Translator" from Text -> Numbers)
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL_NAME
)
print("✅ Download Complete! You are ready for RAG.")
# Create (or get) the Collection (Think of this as a "Table" in SQL)
collection = chroma_client.get_or_create_collection(
    name="character_memory",
    embedding_function=embedding_func
)

def add_memory_to_db(user_id : str,char_id : str, text : str, role : str):
    """
    Stores a single message into the Vector DB.
    We tag it with user_id and char_id so we don't mix up memories!
    """

    # 1. Create a unique ID for this memory
    memory_id = str(uuid.uuid4())

    # 2. Metadata helps us filter later (e.g., "Only show Max's memories of Mario")
    metadata = {
        "user_id": str(user_id),
        "char_id": char_id,
        "role": role, # 'user' or 'ai'
        "timestamp": str(uuid.uuid1().time) # Simple timestamp
    }

    # 3. Add to ChromaDB
    collection.add(
        documents=[text],      # The actual text (e.g., "I like pizza")
        metadatas=[metadata],  # The tags
        ids=[memory_id]        # Unique ID
    )
    print(f"🧠 Memory stored: {text[:30]}...")

def retrieve_relevant_memories(user_id : str , char_id : str, query_text : str, limit :  int = 5):
    """
    The Magic: Finds the top 3 past memories most relevant to the 'query_text'.
    """
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=limit,
            # CRITICAL: Filter so we only get memories for THIS specific user/character pair
            where={
                "$and": [
                    {"user_id": str(user_id)},
                    {"char_id": char_id}
                ]
            }
        )

        # # Extract just the text from the results
        # memories = results['documents'][0]
        # return memories
        # Check if we actually got documents back
        if results['documents'] and len(results['documents'][0]) > 0:
            return results['documents'][0]
        return []
    
    except Exception as e:
        print(f"memory search error : {e}")
        return []
