import os
import hashlib
from datetime import datetime
from app.ingestion.vector_store import get_collection


def get_file_hash(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()[:8]


def get_ingested_documents() -> dict:
    collection = get_collection()
    results = collection.get(include=["metadatas"])
    
    docs = {}
    for metadata in results["metadatas"]:
        doc_id = metadata.get("doc_id")
        file_name = metadata.get("file_name")
        if doc_id and file_name:
            docs[doc_id] = file_name
    return docs


def check_drift(upload_dir: str = "./data/raw") -> dict:
    ingested = get_ingested_documents()
    
    stale = []
    missing = []
    fresh = []

    for doc_id, file_name in ingested.items():
        file_path = os.path.join(upload_dir, file_name)

        if not os.path.exists(file_path):
            missing.append({
                "doc_id": doc_id,
                "file_name": file_name,
                "reason": "File no longer exists on disk",
            })
            continue

        current_hash = get_file_hash(file_path)
        ingested_hash = doc_id.split("_")[-1]

        if current_hash != ingested_hash:
            stale.append({
                "doc_id": doc_id,
                "file_name": file_name,
                "reason": "File has been modified since ingestion",
                "ingested_hash": ingested_hash,
                "current_hash": current_hash,
            })
        else:
            fresh.append({
                "doc_id": doc_id,
                "file_name": file_name,
                "status": "up to date",
            })

    return {
        "checked_at": datetime.utcnow().isoformat(),
        "total_documents": len(ingested),
        "fresh": len(fresh),
        "stale": len(stale),
        "missing": len(missing),
        "stale_documents": stale,
        "missing_documents": missing,
        "fresh_documents": fresh,
    }


if __name__ == "__main__":
    import json
    result = check_drift()
    print(json.dumps(result, indent=2))