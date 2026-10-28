import os
import math
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from pypdf import PdfReader
from backend.app.config import UPLOAD_DIR
from backend.app.database import get_db
from backend.app.models.schemas import (
    DocumentResponse, DocumentChunkResponse, DocumentQueryResponse, StudyGuideResponse
)
from backend.app.services.llm_service import llm_service

def tokenize(text: str) -> List[str]:
    return [w for w in re.findall(r"\b[a-zA-Z0-9_]{3,}\b", text.lower())]

def compute_term_frequencies(tokens: List[str]) -> Dict[str, float]:
    counts: Dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    total = len(tokens) or 1
    return {k: v / total for k, v in counts.items()}

def cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    dot = 0.0
    for k, val1 in v1.items():
        if k in v2:
            dot += val1 * v2[k]
    mag1 = math.sqrt(sum(x * x for x in v1.values())) or 1e-9
    mag2 = math.sqrt(sum(x * x for x in v2.values())) or 1e-9
    return dot / (mag1 * mag2)

class RAGService:
    def process_pdf(self, file_path: Path, original_filename: str) -> DocumentResponse:
        reader = PdfReader(str(file_path))
        num_pages = len(reader.pages)
        file_size = file_path.stat().st_size
        now = datetime.now().isoformat()

        all_text_chunks: List[Tuple[int, str, Dict[str, float]]] = []
        full_text_list = []

        chunk_size = 600
        overlap = 100

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            raw_text = page.extract_text() or ""
            cleaned = " ".join(raw_text.split())
            if not cleaned:
                continue
            full_text_list.append(f"[Page {page_num}]: {cleaned}")

            # Sliding window chunking
            start = 0
            while start < len(cleaned):
                end = min(start + chunk_size, len(cleaned))
                chunk = cleaned[start:end]
                tf = compute_term_frequencies(tokenize(chunk))
                all_text_chunks.append((page_num, chunk, tf))
                if end == len(cleaned):
                    break
                start += chunk_size - overlap

        combined_text = "\n".join(full_text_list)
        initial_summary = self._generate_quick_summary(combined_text, original_filename)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO documents (filename, original_name, file_size, page_count, summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (file_path.name, original_filename, file_size, num_pages, initial_summary, now))
            doc_id = cursor.lastrowid

            for idx, (p_num, content, tf) in enumerate(all_text_chunks):
                cursor.execute("""
                    INSERT INTO document_chunks (document_id, chunk_index, page_number, content, embedding_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (doc_id, idx, p_num, content, json.dumps(tf), now))

            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            return DocumentResponse(**dict(cursor.fetchone()))

    def _generate_quick_summary(self, full_text: str, filename: str) -> str:
        snippet = full_text[:2000]
        dates = re.findall(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b", full_text)
        date_info = f" Mentioned milestones/dates: {', '.join(set(dates[:4]))}." if dates else ""
        return f"Document '{filename}' covering core subject material with {len(snippet)} characters analyzed.{date_info}"

    def list_documents(self) -> List[DocumentResponse]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY id DESC")
            return [DocumentResponse(**dict(r)) for r in cursor.fetchall()]

    def get_document(self, doc_id: int) -> Optional[DocumentResponse]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return DocumentResponse(**dict(row)) if row else None

    def search_chunks(self, query: str, doc_id: Optional[int] = None, top_k: int = 4) -> List[Dict[str, Any]]:
        query_tf = compute_term_frequencies(tokenize(query))
        with get_db() as conn:
            cursor = conn.cursor()
            if doc_id:
                cursor.execute("""
                    SELECT c.id, c.document_id, c.chunk_index, c.page_number, c.content, c.embedding_json, d.original_name
                    FROM document_chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE c.document_id = ?
                """, (doc_id,))
            else:
                cursor.execute("""
                    SELECT c.id, c.document_id, c.chunk_index, c.page_number, c.content, c.embedding_json, d.original_name
                    FROM document_chunks c
                    JOIN documents d ON c.document_id = d.id
                """)
            rows = cursor.fetchall()

        scored = []
        for r in rows:
            chunk_tf = json.loads(r["embedding_json"])
            score = cosine_similarity(query_tf, chunk_tf)
            # Boost score if exact query words appear
            query_words = tokenize(query)
            for w in query_words:
                if w in r["content"].lower():
                    score += 0.15
            scored.append({
                "chunk_id": r["id"],
                "document_id": r["document_id"],
                "document_name": r["original_name"],
                "page_number": r["page_number"],
                "content": r["content"],
                "score": score
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    async def query_document(self, doc_id: int, query: str, top_k: int = 4) -> DocumentQueryResponse:
        doc = self.get_document(doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found.")

        relevant_chunks = self.search_chunks(query, doc_id=doc_id, top_k=top_k)
        citations = []
        context_blocks = []
        for c in relevant_chunks:
            citations.append({
                "page": c["page_number"],
                "excerpt": c["content"][:200] + "...",
                "relevance_score": round(c["score"], 3)
            })
            context_blocks.append(f"[Page {c['page_number']}]: {c['content']}")

        context_str = "\n\n".join(context_blocks)
        prompt = (
            f"You are the NOVA AI Document Intelligence Agent analyzing '{doc.original_name}'.\n"
            f"Relevant passages from the document:\n{context_str}\n\n"
            f"User Question: {query}\n\n"
            "Instructions:\n"
            "1. Answer the question accurately using the provided passages.\n"
            "2. Always cite specific page numbers (e.g. [Page X]) for your statements.\n"
            "3. If the passage explains difficult concepts, break them down clearly.\n"
            "4. Be concise and structured."
        )

        answer = await llm_service.generate_response(
            messages=[{"role": "user", "content": prompt}],
            system_instruction="You are NOVA AI's RAG Document Specialist. Provide clear, page-cited answers."
        )

        related_questions = [
            f"Can you explain the main conclusions on Page {citations[0]['page']}?",
            f"What are key definitions mentioned in {doc.original_name}?",
            "What formulas or algorithms are highlighted in this section?"
        ] if citations else []

        return DocumentQueryResponse(
            query=query,
            answer=answer,
            citations=citations,
            related_questions=related_questions
        )

    def generate_study_guide(self, doc_id: int) -> StudyGuideResponse:
        doc = self.get_document(doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found.")

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT page_number, content FROM document_chunks WHERE document_id = ? ORDER BY chunk_index ASC", (doc_id,))
            chunks = cursor.fetchall()

        all_text = " ".join(c["content"] for c in chunks)
        # Extract dates
        dates = list(set(re.findall(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b", all_text)))
        milestones = [f"Milestone/Date noted: {d}" for d in dates[:5]] or ["No explicit historical dates detected."]

        # Key points extraction
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", all_text) if len(s.strip()) > 30]
        key_points = [f"• {s}." for s in sentences[:5]] or [f"Document '{doc.original_name}' core technical content."]

        # Study questions with page numbers
        study_questions = []
        for i, c in enumerate(chunks[:5]):
            words = tokenize(c["content"])
            topic = words[0].capitalize() if words else "Concept"
            study_questions.append({
                "question": f"Explain the principle of '{topic}' as presented in the text.",
                "answer_page": f"Page {c['page_number']}"
            })

        return StudyGuideResponse(
            document_id=doc.id,
            document_name=doc.original_name,
            summary=doc.summary or f"Comprehensive breakdown of {doc.original_name}",
            key_points=key_points,
            important_dates_and_milestones=milestones,
            study_questions=study_questions
        )

    def delete_document(self, doc_id: int) -> bool:
        doc = self.get_document(doc_id)
        if not doc:
            return False
        
        file_path = UPLOAD_DIR / doc.filename
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception:
                pass

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM document_chunks WHERE document_id = ?", (doc_id,))
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            return cursor.rowcount > 0

rag_service = RAGService()

