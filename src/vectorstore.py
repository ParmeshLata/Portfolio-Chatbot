import hashlib
import chromadb
from chromadb.config import Settings


def setup_vectorstore(chunks, path='./data/chroma_database', name='parmesh_resume'):
    """Sync current source chunks; remove stale documents, including on edits."""
    client = chromadb.PersistentClient(path=path, settings=Settings(anonymized_telemetry=False))
    collection = client.get_or_create_collection(name=name)
    wanted = {}
    for chunk in chunks:
        doc = chunk['text'].strip()
        if not doc:
            continue
        digest = hashlib.sha256((chunk['section'] + '\0' + doc).encode()).hexdigest()[:32]
        wanted[digest] = chunk
    existing = set(collection.get(include=[])['ids'])
    stale = list(existing - set(wanted))
    if stale:
        collection.delete(ids=stale)
    new = [key for key in wanted if key not in existing]
    if new:
        collection.add(ids=new, documents=[wanted[key]['text'] for key in new],
                       metadatas=[{'section': wanted[key]['section']} for key in new])
    return collection


def retrieve(collection, query, limit=3, max_distance=None):
    count = collection.count()
    if not count or not query.strip():
        return []
    result = collection.query(query_texts=[query], n_results=min(limit, count),
                              include=['documents', 'distances'])
    docs = result['documents'][0]
    distances = result['distances'][0]
    return [doc for doc, distance in zip(docs, distances)
            if max_distance is None or distance <= max_distance]
