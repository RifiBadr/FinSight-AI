import os
import json
import pymupdf
import config


def read_pdf(path):
    # returns a list of (page number, text)
    pages = []
    doc = pymupdf.open(path)
    for i, page in enumerate(doc):
        text = " ".join(page.get_text().split())
        if text:
            pages.append((i + 1, text))
    doc.close()
    return pages


def split_text(text, size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        if start + size >= len(text):
            break
        start += size - overlap
    return chunks


def build_chunks(folder):
    chunks = []
    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".pdf"):
            continue
        doc_name = filename.replace(".pdf", "")
        pages = read_pdf(os.path.join(folder, filename))

        # chunk each page separately so every chunk has one page number
        for page_num, text in pages:
            for piece in split_text(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP):
                chunks.append({"id": len(chunks), "doc": doc_name, "page": page_num, "text": piece})

        print(doc_name, "-", len(pages), "pages")
    return chunks


if __name__ == "__main__":
    chunks = build_chunks(config.PDF_FOLDER)

    with open(config.CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f)

    print("total chunks:", len(chunks))
    print(chunks[50])
