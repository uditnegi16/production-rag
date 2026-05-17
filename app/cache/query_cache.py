import os
import json
import hashlib
import redis
from dotenv import load_dotenv

load_dotenv()

_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                _redis_client = redis.from_url(redis_url, decode_responses=True)
                _redis_client.ping()
                print("Redis cache connected.")
            except Exception as e:
                print(f"Redis connection failed, running without cache: {e}")
                _redis_client = None
    return _redis_client


def make_cache_key(query: str, doc_id: str = None) -> str:
    raw = f"{query}::{doc_id or 'all'}"
    return "rag:" + hashlib.md5(raw.encode()).hexdigest()


def get_cached_response(query: str, doc_id: str = None) -> dict:
    client = get_redis_client()
    if not client:
        return None
    try:
        key = make_cache_key(query, doc_id)
        cached = client.get(key)
        if cached:
            print(f"Cache HIT: {key}")
            return json.loads(cached)
    except Exception as e:
        print(f"Cache get error: {e}")
    return None


def set_cached_response(query: str, response: dict, doc_id: str = None, ttl: int = 3600):
    client = get_redis_client()
    if not client:
        return
    try:
        key = make_cache_key(query, doc_id)
        client.setex(key, ttl, json.dumps(response))
        print(f"Cache SET: {key}")
    except Exception as e:
        print(f"Cache set error: {e}")