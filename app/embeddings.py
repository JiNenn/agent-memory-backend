from __future__ import annotations

import hashlib
import math
import re
import unicodedata


def _features(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).lower()
    words = re.findall(r"\w+", normalized, flags=re.UNICODE)
    if words:
        grams: list[str] = []
        for word in words:
            if len(word) <= 3:
                grams.append(word)
                continue
            grams.extend(word[index : index + 3] for index in range(len(word) - 2))
        return grams
    compact = re.sub(r"\s+", "", normalized)
    return [compact[index : index + 3] for index in range(max(len(compact) - 2, 1))]


def embed_text(text: str, dimensions: int = 384) -> list[float]:
    if dimensions <= 0:
        raise ValueError("dimensions must be positive")

    vector = [0.0] * dimensions
    for feature in _features(text):
        digest = hashlib.sha256(feature.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        weight = 1.0 + (digest[5] % 7) / 7.0
        vector[index] += sign * weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]

