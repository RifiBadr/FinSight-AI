import os
import re
import json
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import config
from query_expansion import expand_query

STOPWORDS = {
    "what", "was", "were", "is", "are", "the", "a", "an", "of", "in", "on", "for",
    "to", "and", "or", "how", "much", "many", "did", "does", "do", "which", "who",
    "by", "its", "it", "this", "that", "with", "as", "at", "from", "be", "has", "have",
}


def tokenize(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOPWORDS]


class HybridSearch:
    def __init__(self):
        with open(config.CHUNKS_FILE, encoding="utf-8") as f:
            self.chunks = json.load(f)
        self.chunk_docs = np.array([c["doc"] for c in self.chunks])

        self.bm25 = BM25Okapi([tokenize(c["text"]) for c in self.chunks])
        self.model = SentenceTransformer(config.EMBED_MODEL)
        self.embeddings = self.load_embeddings()

    def load_embeddings(self):
        # embedding all chunks is slow, so save them the first time
        if os.path.exists(config.EMBEDDINGS_FILE):
            embeddings = np.load(config.EMBEDDINGS_FILE)
            if len(embeddings) == len(self.chunks):
                return embeddings
            print("chunks changed, rebuilding embeddings")

        texts = [c["text"] for c in self.chunks]
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
        np.save(config.EMBEDDINGS_FILE, embeddings)
        return embeddings

    def list_documents(self):
        return sorted(set(self.chunk_docs))

    def get_ids(self, doc):
        # all chunks, or only the chunks from one report
        if doc is None:
            return np.arange(len(self.chunks))
        return np.where(self.chunk_docs == doc)[0]

    def keyword_search(self, query, k, doc=None):
        ids = self.get_ids(doc)
        scores = self.bm25.get_scores(tokenize(query))[ids]
        return list(ids[np.argsort(scores)[::-1][:k]])

    def semantic_search(self, query, k, doc=None):
        ids = self.get_ids(doc)
        query_vec = self.model.encode(query, normalize_embeddings=True)
        scores = self.embeddings[ids] @ query_vec
        return list(ids[np.argsort(scores)[::-1][:k]])

    def search(self, query, k=config.TOP_K, doc=None, expand=True):
        keyword_query = expand_query(query) if expand else query
        keyword_ids = self.keyword_search(keyword_query, 50, doc)
        semantic_ids = self.semantic_search(query, 50, doc)

        # reciprocal rank fusion: combine the two rankings
        scores = {}
        for ranking in [keyword_ids, semantic_ids]:
            for rank, i in enumerate(ranking):
                scores[i] = scores.get(i, 0) + 1 / (60 + rank + 1)

        best = sorted(scores, key=scores.get, reverse=True)[:k]
        return [self.chunks[i] for i in best]


if __name__ == "__main__":
    searcher = HybridSearch()
    for q in ["What was 3M's capital expenditure in 2018?", "How much did 3M pay in dividends?"]:
        print("\n" + q)
        for c in searcher.search(q, doc="3M_2018_10K"):
            print(f"  {c['doc']} p.{c['page']}: {c['text'][:80]}...")
