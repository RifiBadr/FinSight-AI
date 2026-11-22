import os
import json
import shutil
import numpy as np

# the live demo uses a smaller set of well-known reports
DEMO_REPORTS = [
    "3M_2018_10K",
    "ADOBE_2022_10K",
    "AMAZON_2019_10K",
    "AMD_2022_10K",
    "BOEING_2022_10K",
    "COCACOLA_2022_10K",
    "MICROSOFT_2023_10K",
    "NETFLIX_2017_10K",
    "NIKE_2023_10K",
    "PEPSICO_2022_10K",
    "VERIZON_2022_10K",
    "WALMART_2020_10K",
]

os.makedirs("demo_data/pdfs", exist_ok=True)

with open("data/chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)
embeddings = np.load("data/embeddings.npy")

# keep only the chunks (and their embeddings) from the demo reports
keep = [i for i, c in enumerate(chunks) if c["doc"] in DEMO_REPORTS]
demo_chunks = []
for new_id, i in enumerate(keep):
    chunk = dict(chunks[i])
    chunk["id"] = new_id
    demo_chunks.append(chunk)

with open("demo_data/chunks.json", "w", encoding="utf-8") as f:
    json.dump(demo_chunks, f)
np.save("demo_data/embeddings.npy", embeddings[keep].astype(np.float32))

for name in DEMO_REPORTS:
    shutil.copy(f"data/pdfs/{name}.pdf", f"demo_data/pdfs/{name}.pdf")

print(len(DEMO_REPORTS), "reports,", len(demo_chunks), "chunks")