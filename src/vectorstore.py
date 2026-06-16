import chromadb
from chromadb.config import Settings
from src.chunker import chunk_projects

def setup_vectorstore(chunks, path="./data/chroma_database"):
    client = chromadb.PersistentClient(
        path=path,
        settings=Settings(anonymized_telemetry=False)
    )
    collection = client.get_or_create_collection(name="parmesh_resume")

    all_chunks = []
    for chunk in chunks:
        if chunk["section"].lower() == "projects":
            for proj in chunk_projects(chunk["text"]):
                all_chunks.append({"section": "Projects", "text": proj})
        else:
            all_chunks.append(chunk)

    if collection.count() == 0:
        for i, chunk in enumerate(all_chunks):
            collection.add(
                documents=[chunk["text"]],
                metadatas=[{"section": chunk["section"]}],
                ids=[f"chunk_{i}"]
            )
        print(f"Stored {len(all_chunks)} chunks in ChromaDB")
    else:
        print(f"Collection already has {collection.count()} chunks, skipping re-index.")
    return collection