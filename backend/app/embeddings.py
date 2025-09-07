import hashlib, math, random
from typing import Iterable

def text_to_vec(text: str, dims: int = 128) -> list[float]:
    h = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    rnd = random.Random(h)
    vec = [rnd.uniform(-1, 1) for _ in range(dims)]
    norm = math.sqrt(sum(v*v for v in vec)) or 1.0
    return [v / norm for v in vec]

def _to_float_list(v: Iterable) -> list[float]:
    # Accept list[float], list[str], or pgvector text like "[0.1,0.2,...]"
    if isinstance(v, str):
        s = v.strip()
        if s.startswith('[') and s.endswith(']'):
            s = s[1:-1]
        parts = [p.strip() for p in s.split(',') if p.strip()]
        return [float(p) for p in parts]
    return [float(x) for x in v]

def cosine(a, b) -> float:
    A = _to_float_list(a)
    B = _to_float_list(b)
    return sum(x*y for x, y in zip(A, B))