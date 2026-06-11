# Reference Documents for RAG Knowledge Base

You can drop any reference materials here to automatically expand the RAG system's knowledge base.

## Supported formats:
- `.txt` (Plain text files)
- `.md` (Markdown files)

## Naming Convention (Highly Recommended):
Prefix the filename with the Topic ID so the RAG reranker can prioritize this file for questions from that topic.
For example:
- `LD_coulomb_theory.txt` (for Coulomb Force & Electric Field)
- `TD_capacitor_formulas.md` (for Capacitor)
- `CHLT_ac_resonance_notes.txt` (for AC Resonance)
- `DDT_electromagnetic_induction.txt` (for Magnetism)
- `THCB_error_theory.txt` (for Measurement Errors)

## How it works:
1. When the pipeline starts, it scans this folder.
2. It splits each document into smaller paragraphs/chunks (approx 400-600 characters).
3. Each chunk is indexed into the search index (BM25 or Qdrant vector index).
4. The topic prefix is parsed from the filename (e.g., `LD_` -> `LD` topic prefix) to boost relevance during topic routing.
