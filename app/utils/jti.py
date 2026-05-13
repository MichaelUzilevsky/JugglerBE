import hashlib
from uuid import uuid4


def new_jti() -> str:
    return str(uuid4())


def hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode("utf-8")).hexdigest()
