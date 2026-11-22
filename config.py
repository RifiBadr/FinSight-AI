import os
from dotenv import load_dotenv

load_dotenv()

# file paths 
DATA_DIR = os.getenv("DATA_DIR", "data")
PDF_FOLDER = DATA_DIR + "/pdfs"
CHUNKS_FILE = DATA_DIR + "/chunks.json"
EMBEDDINGS_FILE = DATA_DIR + "/embeddings.npy"
QUESTIONS_FILE = "data/financebench.jsonl"

# retrieval settings
EMBED_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K = 5

# llm settings (key is in .env)
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
