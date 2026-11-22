import sys
from sentence_transformers import SentenceTransformer
import config

print("Python version:", sys.version.split()[0])

model = SentenceTransformer(config.EMBED_MODEL)
vector = model.encode("Apple's revenue in 2022")

print("Embedding length:", len(vector))
print("API key found:", config.LLM_API_KEY is not None)
print("Setup OK")