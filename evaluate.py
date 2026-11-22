import os
import json
import config
from search import HybridSearch

K = 5


def load_questions():
    with open(config.QUESTIONS_FILE, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def evaluate(search_fn, questions, name):
    hits = 0
    results = []

    for q in questions:
        found = search_fn(q["question"], q["doc_name"])
        found_pages = [(c["doc"], c["page"]) for c in found]

        # financebench pages start at 0, ours start at 1
        gold_pages = [(e["doc_name"], e["evidence_page_num"] + 1) for e in q["evidence"]]

        hit = any(p in gold_pages for p in found_pages)
        hits += hit
        results.append({"question": q["question"], "gold": gold_pages, "found": found_pages, "hit": hit})

    print(f"{name:<16} Hit@{K}: {hits / len(questions):.1%}")

    os.makedirs("results", exist_ok=True)
    with open(f"results/{name}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    questions = load_questions()
    searcher = HybridSearch()
    print("evaluating on", len(questions), "questions\n")

    # we search inside the report the question is about (like picking it in the app)
    evaluate(lambda q, doc: [searcher.chunks[i] for i in searcher.keyword_search(q, K, doc)], questions, "keyword")
    evaluate(lambda q, doc: [searcher.chunks[i] for i in searcher.semantic_search(q, K, doc)], questions, "semantic")
    evaluate(lambda q, doc: searcher.search(q, K, doc, expand=False), questions, "hybrid")
    evaluate(lambda q, doc: searcher.search(q, K, doc, expand=True), questions, "hybrid_expanded")
