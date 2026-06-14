"""
Knowledge Base: Load, index, and search physics formulas.
Supports two backends:
  - In-memory (default, no external deps)
  - Qdrant (production, requires qdrant-client)
"""
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

from app.config import config


@dataclass
class KBEntry:
    """A single searchable knowledge item."""
    topic_prefix: str       # "LD", "CH", etc.
    topic_name: str         # "Electrostatics — Coulomb Force..."
    law_name: str           # "Coulomb's Law"
    formula: str            # "F = k * |q1 * q2| / r^2"
    latex: str = ""
    description: str = ""
    units: str = ""
    constants: str = ""
    notes: str = ""
    answer_type: str = ""

    @property
    def text(self) -> str:
        """Combine all fields into a single searchable string."""
        parts = [
            f"[{self.topic_prefix}] {self.law_name}",
            f"Formula: {self.formula}",
        ]
        if self.latex:
            parts.append(f"LaTeX: {self.latex}")
        if self.description:
            parts.append(self.description)
        if self.units:
            parts.append(f"Units: {self.units}")
        if self.constants:
            parts.append(f"Constants: {self.constants}")
        if self.notes:
            parts.append(f"Note: {self.notes}")
        if self.answer_type:
            parts.append(f"Answer type: {self.answer_type}")
        return " | ".join(parts)

    @property
    def premise_string(self) -> str:
        """Format as a premise for the API response."""
        premise = f"{self.law_name}: {self.formula}"
        if self.description:
            premise += f" | Use: {self.description}"
        if self.notes:
            premise += f" | Note: {self.notes}"
        if self.answer_type:
            premise += f" | Answer type: {self.answer_type}"
        return premise


class InMemoryKB:
    """
    In-memory knowledge base with BM25-style keyword search.
    No external dependencies required — works immediately.
    """

    def __init__(self):
        self.entries: List[KBEntry] = []
        self._idf: dict = {}
        self._doc_tfs: List[dict] = []
        self._avg_dl: float = 0.0

    def load_from_json(self, path: Path) -> int:
        """Load knowledge base from the curated JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        kb_data = data.get("knowledge_base", data)
        topics = kb_data.get("topics", [])

        for topic in topics:
            prefix = topic.get("prefix", "")
            topic_name = topic.get("topic", "")
            for law in topic.get("laws", []):
                entry = KBEntry(
                    topic_prefix=prefix,
                    topic_name=topic_name,
                    law_name=law.get("name", ""),
                    formula=law.get("formula", ""),
                    latex=law.get("latex", ""),
                    description=law.get("description", ""),
                    units=law.get("units", ""),
                    constants=law.get("constant", ""),
                    notes=law.get("note", ""),
                    answer_type=law.get("answer_type", ""),
                )
                self.entries.append(entry)

        # Also add unit conversions as searchable entries
        conversions = kb_data.get("unit_conversions", {}).get("conversions", [])
        if conversions:
            self.entries.append(KBEntry(
                topic_prefix="ALL",
                topic_name="Unit Conversions",
                law_name="SI Unit Conversion Table",
                formula="; ".join(conversions),
                description="Always convert to SI units before calculation",
                answer_type="quantitative",
            ))

        # Dynamically load external reference documents
        ref_dir = path.parent / "reference_docs"
        if ref_dir.is_dir():
            self._load_reference_docs(ref_dir)

        # Build BM25 index
        self._build_index()
        return len(self.entries)

    def _load_reference_docs(self, ref_dir: Path):
        """Scan and load external txt/md reference files from ref_dir."""
        import glob
        files = glob.glob(str(ref_dir / "*.*"))
        loaded_files = 0
        loaded_chunks = 0

        for fpath_str in files:
            fpath = Path(fpath_str)
            if fpath.suffix.lower() not in [".txt", ".md"]:
                continue

            # Detect topic prefix from filename (e.g., LD_coulomb.txt -> LD)
            filename = fpath.stem
            prefix_match = re.match(r"^([a-zA-Z]+)_", filename)
            topic_prefix = prefix_match.group(1).upper() if prefix_match else "REF"
            
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"[KB] Warning: Failed to read {fpath.name}: {e}")
                continue

            # Split into paragraphs/chunks
            paragraphs = re.split(r"\n\s*\n", content)
            chunks = []
            for p in paragraphs:
                p_clean = p.strip()
                if not p_clean or len(p_clean) < 15:
                    continue
                # If paragraph is too long, split by characters/sentences (e.g., max 600 chars)
                if len(p_clean) > 800:
                    sub_chunks = []
                    words = p_clean.split()
                    current_chunk = []
                    current_len = 0
                    for word in words:
                        current_chunk.append(word)
                        current_len += len(word) + 1
                        if current_len >= 600:
                            sub_chunks.append(" ".join(current_chunk))
                            current_chunk = []
                            current_len = 0
                    if current_chunk:
                        sub_chunks.append(" ".join(current_chunk))
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(p_clean)

            # Register chunks as KB entries
            for idx, chunk in enumerate(chunks):
                entry = KBEntry(
                    topic_prefix=topic_prefix,
                    topic_name=f"Reference Doc: {filename}",
                    law_name=f"Excerpt from {filename} (part {idx+1})",
                    formula="",
                    description=chunk,
                    notes=f"Source: reference_docs/{fpath.name}",
                    answer_type="reference",
                )
                self.entries.append(entry)
                loaded_chunks += 1
            loaded_files += 1

        if loaded_files > 0:
            print(f"[KB] Loaded {loaded_chunks} chunks from {loaded_files} reference files in reference_docs/")

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25."""
        text = text.lower()
        # Keep important symbols
        text = re.sub(r"[^\w\s=/*^+\-]", " ", text)
        tokens = text.split()
        return [t for t in tokens if len(t) > 1]

    def _build_index(self):
        """Build BM25 inverted index."""
        N = len(self.entries)
        if N == 0:
            return

        # Compute term frequencies per document
        self._doc_tfs = []
        doc_lengths = []
        df = {}  # document frequency

        for entry in self.entries:
            tokens = self._tokenize(entry.text)
            doc_lengths.append(len(tokens))
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self._doc_tfs.append(tf)
            for t in set(tokens):
                df[t] = df.get(t, 0) + 1

        self._avg_dl = sum(doc_lengths) / N if N > 0 else 1.0

        # Compute IDF
        self._idf = {}
        for term, freq in df.items():
            self._idf[term] = math.log((N - freq + 0.5) / (freq + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[KBEntry, float]]:
        """
        BM25 search over the knowledge base.
        
        Returns:
            List of (entry, score) tuples, sorted by relevance.
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        k1 = 1.5
        b = 0.75
        scores = []

        for i, (entry, tf_dict) in enumerate(zip(self.entries, self._doc_tfs)):
            score = 0.0
            dl = sum(tf_dict.values())
            for qt in query_tokens:
                if qt in tf_dict:
                    tf = tf_dict[qt]
                    idf = self._idf.get(qt, 0.0)
                    numerator = tf * (k1 + 1)
                    denominator = tf + k1 * (1 - b + b * dl / self._avg_dl)
                    score += idf * numerator / denominator
            scores.append((entry, score))

        # Sort by score descending, return top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ─── Qdrant Vector Knowledge Base ───
class QdrantKB:
    """
    Qdrant-backed vector database for semantic RAG search.
    Requires qdrant-client and sentence-transformers.
    Automatically falls back to InMemoryKB if Qdrant server is offline.
    """

    def __init__(self):
        self.entries: List[KBEntry] = []
        self.client = None
        self.model = None
        self.fallback_kb = None

    def _init_qdrant(self) -> bool:
        """Connect to Qdrant server and load embedding model."""
        try:
            from qdrant_client import QdrantClient
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            print(f"[QdrantKB] Missing dependencies ({e}). Falling back to InMemoryKB.")
            return False

        try:
            if config.qdrant_host.startswith(("http://", "https://")):
                self.client = QdrantClient(
                    url=config.qdrant_host,
                    api_key=config.qdrant_api_key or None,
                    timeout=8.0,
                )
            else:
                self.client = QdrantClient(
                    host=config.qdrant_host,
                    port=config.qdrant_port,
                    api_key=config.qdrant_api_key or None,
                    timeout=8.0
                )
            # Ping client
            self.client.get_collections()
        except Exception as e:
            print(f"[QdrantKB] Connection failed to {config.qdrant_host} ({e}). "
                  f"Falling back to InMemoryKB.")
            return False

        # Load embedding model
        model_name = config.embedding_model
        print(f"[QdrantKB] Loading embedding model '{model_name}' (this might take a moment)...")
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            # Fallback to smaller model if main model fails or runs out of VRAM/memory
            fallback_model = "sentence-transformers/all-MiniLM-L6-v2"
            print(f"[QdrantKB] Warning: Failed to load '{model_name}' ({e}). "
                  f"Trying lightweight fallback '{fallback_model}'...")
            try:
                self.model = SentenceTransformer(fallback_model)
            except Exception as fe:
                print(f"[QdrantKB] Error: Failed to load fallback model ({fe}).")
                return False

        return True

    def _collection_is_ready(self, vector_size: int) -> bool:
        """Return True when the existing Qdrant collection matches this KB."""
        collection_name = config.qdrant_collection
        try:
            if not self.client.collection_exists(collection_name=collection_name):
                return False

            info = self.client.get_collection(collection_name=collection_name)
            points_count = getattr(info, "points_count", 0) or 0
            vectors_config = info.config.params.vectors
            existing_size = getattr(vectors_config, "size", None)

            return points_count == len(self.entries) and existing_size == vector_size
        except Exception as e:
            print(f"[QdrantKB] Collection readiness check failed ({e}). Rebuilding index.")
            return False

    def load_from_json(self, path: Path) -> int:
        """Load entries, vectorize them, and index in Qdrant."""
        # Initialize InMemoryKB as a parser and fallback mechanism
        self.fallback_kb = InMemoryKB()
        self.fallback_kb.load_from_json(path)
        self.entries = self.fallback_kb.entries

        if not self._init_qdrant():
            self.client = None
            return len(self.entries)

        try:
            from qdrant_client.models import Distance, VectorParams, PointStruct

            # Re-create collection
            collection_name = config.qdrant_collection
            if hasattr(self.model, "get_embedding_dimension"):
                vector_size = self.model.get_embedding_dimension()
            else:
                vector_size = self.model.get_sentence_embedding_dimension()

            if self._collection_is_ready(vector_size):
                print(
                    f"[QdrantKB] Reusing existing collection '{collection_name}' "
                    f"({len(self.entries)} entries)."
                )
                return len(self.entries)
            
            print(f"[QdrantKB] Initializing collection '{collection_name}' (dim={vector_size})...")
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

            # Generate vectors
            print(f"[QdrantKB] Generating embeddings for {len(self.entries)} entries...")
            texts = [entry.text for entry in self.entries]
            embeddings = self.model.encode(texts, show_progress_bar=False)

            # Upsert
            points = []
            for idx, (entry, vector) in enumerate(zip(self.entries, embeddings)):
                payload = {
                    "topic_prefix": entry.topic_prefix,
                    "topic_name": entry.topic_name,
                    "law_name": entry.law_name,
                    "formula": entry.formula,
                    "latex": entry.latex,
                    "description": entry.description,
                    "units": entry.units,
                    "constants": entry.constants,
                    "notes": entry.notes,
                    "answer_type": entry.answer_type,
                }
                points.append(
                    PointStruct(
                        id=idx,
                        vector=vector.tolist(),
                        payload=payload
                    )
                )

            self.client.upsert(collection_name=collection_name, points=points)
            print(f"[QdrantKB] Successfully indexed {len(points)} entries in Qdrant.")
        except Exception as e:
            print(f"[QdrantKB] Failed indexing in Qdrant ({e}). Using in-memory fallback.")
            self.client = None

        return len(self.entries)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[KBEntry, float]]:
        """Search vector DB using cosine similarity, falling back to BM25 if offline."""
        if not self.client:
            return self.fallback_kb.search(query, top_k=top_k)

        try:
            collection_name = config.qdrant_collection
            query_vector = self.model.encode(query, show_progress_bar=False).tolist()

            if hasattr(self.client, "query_points"):
                query_response = self.client.query_points(
                    collection_name=collection_name,
                    query=query_vector,
                    limit=top_k,
                    with_payload=True,
                )
                results = query_response.points
            else:
                results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                )

            matches = []
            for hit in results:
                payload = hit.payload
                entry = KBEntry(
                    topic_prefix=payload.get("topic_prefix", ""),
                    topic_name=payload.get("topic_name", ""),
                    law_name=payload.get("law_name", ""),
                    formula=payload.get("formula", ""),
                    latex=payload.get("latex", ""),
                    description=payload.get("description", ""),
                    units=payload.get("units", ""),
                    constants=payload.get("constants", ""),
                    notes=payload.get("notes", ""),
                    answer_type=payload.get("answer_type", ""),
                )
                matches.append((entry, hit.score * 10.0))
            return matches
        except Exception as e:
            print(f"[QdrantKB] Search failed ({e}). Falling back to BM25 search.")
            return self.fallback_kb.search(query, top_k=top_k)


# ─── Factory ───
_kb_instance = None


def get_knowledge_base():
    """Get or create the singleton knowledge base (InMemoryKB or QdrantKB)."""
    global _kb_instance
    if _kb_instance is None:
        if config.use_qdrant:
            print("[KB] Initializing Qdrant Vector Knowledge Base...")
            _kb_instance = QdrantKB()
        else:
            print("[KB] Initializing In-Memory BM25 Knowledge Base...")
            _kb_instance = InMemoryKB()
        
        count = _kb_instance.load_from_json(config.kb_path)
        print(f"[KB] Loaded {count} total entries (curated laws + conversions + reference_docs)")
    return _kb_instance
