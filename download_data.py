import os
import json
import urllib.request
import config

BASE_URL = "https://raw.githubusercontent.com/patronus-ai/financebench/main"

os.makedirs(config.PDF_FOLDER, exist_ok=True)

# download the 150 questions
if not os.path.exists(config.QUESTIONS_FILE):
    urllib.request.urlretrieve(BASE_URL + "/data/financebench_open_source.jsonl", config.QUESTIONS_FILE)

with open(config.QUESTIONS_FILE, encoding="utf-8") as f:
    questions = [json.loads(line) for line in f]

# download only the pdfs that the questions use
doc_names = sorted(set(q["doc_name"] for q in questions))
print(len(questions), "questions,", len(doc_names), "documents")

for name in doc_names:
    path = os.path.join(config.PDF_FOLDER, name + ".pdf")
    if not os.path.exists(path):
        print("downloading", name)
        urllib.request.urlretrieve(BASE_URL + "/pdfs/" + name + ".pdf", path)

print("done")
