"""
GraphRAG Policy Knowledge Store.
Loads, chunks, embeds, and indexes Bank Policies & FinCEN Guidelines into TigerGraph PolicyDoc vertices.
Supports hybrid vector and keyword semantic search.
"""

import os
import re
import math
import hashlib
from typing import List, Dict, Any, Optional
from tigergraph.client import TigerGraphClient


def generate_deterministic_embedding(text: str, dim: int = 16) -> List[float]:
    """
    Generates a deterministic normalized semantic embedding vector from text.
    Uses SHA-256 multi-hash projection for consistent, reproducible vector similarity.
    """
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    words = cleaned.split()
    vec = [0.0] * dim

    for i, word in enumerate(words):
        h = hashlib.sha256(word.encode("utf-8")).hexdigest()
        for d in range(dim):
            val = int(h[d * 2 : d * 2 + 2], 16) / 255.0 - 0.5
            vec[d] += val * (1.0 / math.sqrt(i + 1))

    # Normalize vector
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0.0:
        vec = [round(x / norm, 4) for x in vec]
    else:
        vec = [1.0 / math.sqrt(dim)] * dim
    return vec


class PolicyStore:
    def __init__(self, tg_client: Optional[TigerGraphClient] = None, docs_dir: Optional[str] = None):
        self.tg_client = tg_client or TigerGraphClient()
        self.docs_dir = docs_dir or os.path.join(os.path.dirname(__file__), "docs")
        self.policies: Dict[str, Dict[str, Any]] = {}
        self._load_and_index_policies()

    def _load_and_index_policies(self) -> None:
        """Reads markdown files in docs/ and indexes them as PolicyDoc vertices."""
        if not os.path.exists(self.docs_dir):
            return

        for fname in os.listdir(self.docs_dir):
            if fname.endswith(".md"):
                fpath = os.path.join(self.docs_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Split on section headings
                sections = re.split(r"(?=\n##\s+)", content)
                for sec in sections:
                    sec = sec.strip()
                    if not sec:
                        continue
                    # Extract title and clause
                    lines = sec.split("\n")
                    header = lines[0].replace("#", "").strip()
                    clause_match = re.search(r"Clause\s+([\d\.]+)", sec)
                    clause_id = clause_match.group(1) if clause_match else f"{fname}:{header[:10]}"
                    policy_id = f"POL-{hashlib.md5(header.encode()).hexdigest()[:8]}"

                    embedding = generate_deterministic_embedding(sec)
                    record = {
                        "policy_id": policy_id,
                        "title": header,
                        "clause_id": clause_id,
                        "text_content": sec,
                        "embedding": embedding,
                    }
                    self.policies[policy_id] = record

                    # Index into graph as PolicyDoc vertex
                    self.tg_client.upsert_vertex("PolicyDoc", policy_id, record)

    def search_policies(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Hybrid vector search and keyword match over policy clauses."""
        q_vec = generate_deterministic_embedding(query)
        q_words = set(re.findall(r"\w+", query.lower()))
        results = []

        for p_id, p_data in self.policies.items():
            emb = p_data["embedding"]
            # Cosine similarity
            dot = sum(a * b for a, b in zip(q_vec, emb))
            # Keyword overlap boost
            content_words = set(re.findall(r"\w+", p_data["text_content"].lower()))
            overlap = len(q_words.intersection(content_words)) / max(len(q_words), 1)
            hybrid_score = 0.6 * dot + 0.4 * overlap

            results.append({
                "policy_id": p_id,
                "title": p_data["title"],
                "clause_id": p_data["clause_id"],
                "text_content": p_data["text_content"],
                "score": round(hybrid_score, 4),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
