# indexer.py
# Sigma DataTech — Data Catalogue FAISS Indexer

from datetime import date, timedelta
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from snowflake_catalog import TABLE_CATALOG


def build_documents() -> list[Document]:
    documents = []
    for table in TABLE_CATALOG:
        doc = Document(
            page_content=table["description"],
            metadata={
                "table_name":     table["table_name"],
                "last_updated":   table["last_updated"],
                "classification": table["classification"],
                "domain":         table["domain"],
                "owner":          table["owner"],
            }
        )
        documents.append(doc)
    return documents


def build_index() -> FAISS:
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    docs = build_documents()
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore


def search_catalog(query: str, vectorstore: FAISS, k: int = 5) -> list:
    results = vectorstore.similarity_search_with_score(query, k=k)
    return results


def search_recent_tables(vectorstore: FAISS, days: int = 7, k: int = 20) -> list[dict]:
    cutoff = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")

    raw = vectorstore.similarity_search_with_score(
        "tables modified updated recently ingested new data", k=k
    )

    recent = []
    for doc, score in raw:
        if doc.metadata.get("last_updated", "") >= cutoff:
            recent.append({
                "table_name":     doc.metadata["table_name"],
                "last_updated":   doc.metadata["last_updated"],
                "classification": doc.metadata["classification"],
                "domain":         doc.metadata["domain"],
                "score":          round(score, 4),
            })

    recent.sort(key=lambda x: x["last_updated"], reverse=True)
    return recent


if __name__ == "__main__":
    print("Building FAISS index for Sigma DataTech catalogue...")
    vs = build_index()
    if vs is None:
        print("ERROR: build_index() returned None.")
    else:
        print(f"Index built. Total documents: {vs.index.ntotal}")

        print("\n--- Query: 'Which tables contain customer PII?' ---")
        results = search_catalog("Which tables contain customer PII?", vs, k=6)
        for doc, score in results:
            print(f"  [{score:.4f}] {doc.metadata['table_name']} — {doc.metadata['classification']}")

        print("\n--- Recent tables (last 7 days, metadata filter) ---")
        recent = search_recent_tables(vs, days=7)
        for t in recent:
            print(f"  {t['last_updated']}  {t['table_name']} ({t['classification']})")
