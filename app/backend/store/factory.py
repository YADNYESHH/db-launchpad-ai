import os
from functools import lru_cache

from .base import Store
from .memory import InMemoryStore


@lru_cache
def get_store() -> Store:
    backend = os.environ.get("STORE_BACKEND", "memory").lower()
    if backend == "firestore":
        from .firestore_store import FirestoreStore

        project_id = os.environ["PROJECT_ID"]
        return FirestoreStore(project_id=project_id)
    return InMemoryStore()
