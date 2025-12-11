"""
Vector Search Service

Enhanced vector database service for medical knowledge:
- Embedding generation
- Semantic search
- Medical knowledge indexing
- Hybrid search (semantic + keyword)
- RAG (Retrieval-Augmented Generation) support

EPIC-009: US-009.5 Vector Database & Semantic Search
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import hashlib
import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Types of documents in the knowledge base."""
    CLINICAL_GUIDELINE = "clinical_guideline"
    DRUG_INFO = "drug_info"
    MEDICAL_LITERATURE = "medical_literature"
    PROTOCOL = "protocol"
    POLICY = "policy"
    FAQ = "faq"
    PATIENT_EDUCATION = "patient_education"
    PROCEDURE = "procedure"
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"


class EvidenceLevel(str, Enum):
    """Evidence level for medical content."""
    LEVEL_A = "A"  # Highest - Multiple RCTs
    LEVEL_B = "B"  # Single RCT or multiple observational
    LEVEL_C = "C"  # Expert opinion
    LEVEL_D = "D"  # Unclassified
    NOT_APPLICABLE = "N/A"


@dataclass
class DocumentChunk:
    """A chunk of a document for vector indexing."""
    chunk_id: str
    document_id: str
    text: str
    embedding: Optional[List[float]] = None

    # Position
    chunk_index: int = 0
    start_offset: int = 0
    end_offset: int = 0

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MedicalDocument:
    """A medical document in the knowledge base."""
    document_id: str
    tenant_id: str
    title: str
    content: str
    document_type: DocumentType

    # Medical metadata
    specialty: Optional[str] = None  # Cardiology, Oncology, etc.
    condition_codes: List[str] = field(default_factory=list)  # ICD-10
    procedure_codes: List[str] = field(default_factory=list)  # CPT
    snomed_codes: List[str] = field(default_factory=list)  # SNOMED CT
    drug_codes: List[str] = field(default_factory=list)  # RxNorm

    # Source
    source: Optional[str] = None  # "AHA Guidelines 2024"
    source_url: Optional[str] = None
    author: Optional[str] = None
    publication_date: Optional[datetime] = None

    # Evidence
    evidence_level: EvidenceLevel = EvidenceLevel.NOT_APPLICABLE

    # Indexing
    chunks: List[DocumentChunk] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    indexed_at: Optional[datetime] = None

    # Status
    is_indexed: bool = False


@dataclass
class SearchResult:
    """A search result with relevance scoring."""
    chunk_id: str
    document_id: str
    text: str

    # Scores
    similarity_score: float = 0.0  # Vector similarity
    keyword_score: float = 0.0  # BM25/TF-IDF score
    combined_score: float = 0.0  # Hybrid score

    # Context
    document_title: str = ""
    document_type: Optional[DocumentType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Medical relevance
    specialty: Optional[str] = None
    evidence_level: Optional[EvidenceLevel] = None
    source: Optional[str] = None


@dataclass
class SearchQuery:
    """Search query with filters."""
    query: str
    top_k: int = 10

    # Filters
    document_types: Optional[List[DocumentType]] = None
    specialties: Optional[List[str]] = None
    evidence_levels: Optional[List[EvidenceLevel]] = None
    condition_codes: Optional[List[str]] = None  # ICD-10
    procedure_codes: Optional[List[str]] = None  # CPT

    # Search configuration
    use_semantic: bool = True
    use_keyword: bool = True
    semantic_weight: float = 0.7  # Weight for semantic vs keyword
    min_similarity: float = 0.5  # Minimum similarity threshold

    # Reranking
    rerank: bool = True
    rerank_top_k: int = 50  # Get more results before reranking


@dataclass
class RAGContext:
    """Context for RAG (Retrieval-Augmented Generation)."""
    query: str
    search_results: List[SearchResult]

    # Formatted context
    context_text: str = ""

    # Metadata
    sources: List[Dict[str, str]] = field(default_factory=list)
    total_chunks: int = 0
    total_tokens_estimate: int = 0


class VectorSearchService:
    """
    Vector Search Service for medical knowledge retrieval.

    Provides:
    - Document indexing with chunking
    - Embedding generation
    - Semantic search
    - Hybrid search (semantic + keyword)
    - Medical knowledge RAG support
    """

    def __init__(
        self,
        embedding_dimensions: int = 384,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        embedding_model: str = "text-embedding-3-small",
    ):
        self.embedding_dimensions = embedding_dimensions
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = embedding_model

        # In-memory storage (in production, use Pinecone/Chroma/pgvector)
        self._documents: Dict[str, MedicalDocument] = {}
        self._chunks: Dict[str, DocumentChunk] = {}
        self._embeddings: Dict[str, List[float]] = {}

        # Inverted index for keyword search
        self._inverted_index: Dict[str, List[str]] = defaultdict(list)

        # Pre-load some medical knowledge
        self._load_default_knowledge()

    def _load_default_knowledge(self):
        """Load default medical knowledge base."""
        # Sample clinical guidelines
        sample_docs = [
            {
                "title": "Hypertension Management Guidelines",
                "content": """
                Blood pressure targets for most adults should be less than 130/80 mmHg.
                First-line medications include thiazide diuretics, ACE inhibitors, ARBs, and calcium channel blockers.
                Lifestyle modifications are recommended for all patients including DASH diet, sodium restriction,
                weight loss if overweight, regular physical activity, and moderate alcohol consumption.
                For patients with diabetes or chronic kidney disease, ACE inhibitors or ARBs are preferred.
                Regular monitoring and medication adjustment is essential for achieving blood pressure goals.
                """,
                "document_type": DocumentType.CLINICAL_GUIDELINE,
                "specialty": "Cardiology",
                "condition_codes": ["I10", "I11"],
                "source": "ACC/AHA Guidelines 2024",
                "evidence_level": EvidenceLevel.LEVEL_A,
            },
            {
                "title": "Type 2 Diabetes Treatment Protocol",
                "content": """
                Metformin remains the first-line medication for type 2 diabetes when not contraindicated.
                Target HbA1c should be individualized, typically less than 7% for most adults.
                GLP-1 receptor agonists or SGLT2 inhibitors are recommended for patients with
                established cardiovascular disease or high cardiovascular risk.
                SGLT2 inhibitors provide cardiorenal protection and are preferred in heart failure or CKD.
                Regular A1C testing every 3-6 months is recommended to monitor glycemic control.
                Annual comprehensive foot exams and retinal screening are essential.
                """,
                "document_type": DocumentType.CLINICAL_GUIDELINE,
                "specialty": "Endocrinology",
                "condition_codes": ["E11", "E11.9"],
                "source": "ADA Standards of Care 2024",
                "evidence_level": EvidenceLevel.LEVEL_A,
            },
            {
                "title": "Chest Pain Evaluation Protocol",
                "content": """
                Acute chest pain requires rapid assessment to rule out acute coronary syndrome (ACS).
                High-sensitivity troponin testing should be performed immediately.
                12-lead ECG should be obtained within 10 minutes of presentation.
                Risk stratification using HEART score helps determine disposition.
                Low-risk patients (HEART score 0-3) may be suitable for early discharge.
                High-risk features include ST changes, positive troponin, hemodynamic instability.
                Patients with STEMI require immediate activation of cardiac catheterization lab.
                """,
                "document_type": DocumentType.PROTOCOL,
                "specialty": "Emergency Medicine",
                "condition_codes": ["R07.9", "I21", "I20.9"],
                "source": "Hospital Protocol Manual",
                "evidence_level": EvidenceLevel.LEVEL_B,
            },
            {
                "title": "Metformin Drug Information",
                "content": """
                Metformin hydrochloride is a biguanide antidiabetic medication.
                Mechanism: Decreases hepatic glucose production and increases insulin sensitivity.
                Starting dose: 500 mg once or twice daily, titrate slowly to reduce GI side effects.
                Maximum dose: 2550 mg daily in divided doses.
                Common side effects: Nausea, diarrhea, abdominal discomfort, B12 deficiency.
                Contraindications: eGFR less than 30, acute or chronic metabolic acidosis.
                Hold before contrast procedures in patients with eGFR 30-60.
                Monitor: Renal function, B12 levels annually.
                """,
                "document_type": DocumentType.DRUG_INFO,
                "specialty": "Pharmacy",
                "drug_codes": ["6809"],  # RxNorm
                "condition_codes": ["E11"],
                "source": "Drug Monograph",
                "evidence_level": EvidenceLevel.NOT_APPLICABLE,
            },
            {
                "title": "Asthma Action Plan Guidelines",
                "content": """
                Green Zone (doing well): No symptoms, peak flow 80-100% of personal best.
                Continue daily controller medications as prescribed.
                Yellow Zone (getting worse): Some symptoms, peak flow 50-79%.
                Continue controller medications, add quick-relief inhaler every 4-6 hours.
                Call healthcare provider if not improving in 24-48 hours.
                Red Zone (medical alert): Severe symptoms, peak flow below 50%.
                Take quick-relief medication immediately, seek emergency care.
                Step-up therapy may be needed for persistent symptoms.
                Review inhaler technique at every visit.
                """,
                "document_type": DocumentType.PATIENT_EDUCATION,
                "specialty": "Pulmonology",
                "condition_codes": ["J45", "J45.909"],
                "source": "NAEPP Guidelines",
                "evidence_level": EvidenceLevel.LEVEL_A,
            },
        ]

        # Index sample documents
        for doc_data in sample_docs:
            self._index_document_sync(
                tenant_id="default",
                **doc_data,
            )

    def _index_document_sync(
        self,
        tenant_id: str,
        title: str,
        content: str,
        document_type: DocumentType,
        specialty: Optional[str] = None,
        condition_codes: Optional[List[str]] = None,
        procedure_codes: Optional[List[str]] = None,
        drug_codes: Optional[List[str]] = None,
        source: Optional[str] = None,
        evidence_level: EvidenceLevel = EvidenceLevel.NOT_APPLICABLE,
    ) -> MedicalDocument:
        """Synchronously index a document (for initialization)."""
        doc = MedicalDocument(
            document_id=str(uuid4()),
            tenant_id=tenant_id,
            title=title,
            content=content,
            document_type=document_type,
            specialty=specialty,
            condition_codes=condition_codes or [],
            procedure_codes=procedure_codes or [],
            drug_codes=drug_codes or [],
            source=source,
            evidence_level=evidence_level,
        )

        # Chunk the document
        chunks = self._chunk_text(doc.content, doc.document_id)
        doc.chunks = chunks

        # Generate mock embeddings
        for chunk in chunks:
            embedding = self._generate_mock_embedding(chunk.text)
            chunk.embedding = embedding
            self._embeddings[chunk.chunk_id] = embedding
            self._chunks[chunk.chunk_id] = chunk

            # Build inverted index
            words = self._tokenize(chunk.text)
            for word in words:
                self._inverted_index[word].append(chunk.chunk_id)

        # Extract keywords
        doc.keywords = self._extract_keywords(doc.content)

        doc.is_indexed = True
        doc.indexed_at = datetime.now(timezone.utc)

        self._documents[doc.document_id] = doc
        return doc

    async def index_document(
        self,
        tenant_id: str,
        title: str,
        content: str,
        document_type: DocumentType,
        specialty: Optional[str] = None,
        condition_codes: Optional[List[str]] = None,
        procedure_codes: Optional[List[str]] = None,
        snomed_codes: Optional[List[str]] = None,
        drug_codes: Optional[List[str]] = None,
        source: Optional[str] = None,
        source_url: Optional[str] = None,
        author: Optional[str] = None,
        publication_date: Optional[datetime] = None,
        evidence_level: EvidenceLevel = EvidenceLevel.NOT_APPLICABLE,
    ) -> MedicalDocument:
        """
        Index a medical document.

        Args:
            tenant_id: Tenant identifier
            title: Document title
            content: Document content
            document_type: Type of document
            specialty: Medical specialty
            condition_codes: ICD-10 codes
            procedure_codes: CPT codes
            snomed_codes: SNOMED CT codes
            drug_codes: RxNorm codes
            source: Source reference
            source_url: Source URL
            author: Document author
            publication_date: Publication date
            evidence_level: Evidence level

        Returns:
            Indexed MedicalDocument
        """
        doc = MedicalDocument(
            document_id=str(uuid4()),
            tenant_id=tenant_id,
            title=title,
            content=content,
            document_type=document_type,
            specialty=specialty,
            condition_codes=condition_codes or [],
            procedure_codes=procedure_codes or [],
            snomed_codes=snomed_codes or [],
            drug_codes=drug_codes or [],
            source=source,
            source_url=source_url,
            author=author,
            publication_date=publication_date,
            evidence_level=evidence_level,
        )

        # Chunk the document
        chunks = self._chunk_text(doc.content, doc.document_id)
        doc.chunks = chunks

        # Generate embeddings for each chunk
        for chunk in chunks:
            embedding = await self._generate_embedding(chunk.text)
            chunk.embedding = embedding
            self._embeddings[chunk.chunk_id] = embedding
            self._chunks[chunk.chunk_id] = chunk

            # Update metadata
            chunk.metadata = {
                "document_title": title,
                "document_type": document_type.value,
                "specialty": specialty,
                "evidence_level": evidence_level.value,
                "source": source,
            }

            # Build inverted index
            words = self._tokenize(chunk.text)
            for word in words:
                self._inverted_index[word].append(chunk.chunk_id)

        # Extract keywords
        doc.keywords = self._extract_keywords(doc.content)

        doc.is_indexed = True
        doc.indexed_at = datetime.now(timezone.utc)

        self._documents[doc.document_id] = doc

        logger.info(
            f"Indexed document {doc.document_id}: {title} "
            f"({len(chunks)} chunks)"
        )

        return doc

    def _chunk_text(
        self,
        text: str,
        document_id: str,
    ) -> List[DocumentChunk]:
        """Split text into chunks with overlap."""
        chunks = []
        text = text.strip()

        # Split into sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = ""
        current_start = 0
        chunk_index = 0

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                # Save current chunk
                if current_chunk.strip():
                    chunks.append(DocumentChunk(
                        chunk_id=str(uuid4()),
                        document_id=document_id,
                        text=current_chunk.strip(),
                        chunk_index=chunk_index,
                        start_offset=current_start,
                        end_offset=current_start + len(current_chunk),
                    ))
                    chunk_index += 1

                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                current_start = current_start + len(current_chunk) - len(overlap_text)
                current_chunk = overlap_text + sentence + " "

        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(DocumentChunk(
                chunk_id=str(uuid4()),
                document_id=document_id,
                text=current_chunk.strip(),
                chunk_index=chunk_index,
                start_offset=current_start,
                end_offset=current_start + len(current_chunk),
            ))

        return chunks

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        # In production, call OpenAI/local embedding model
        # For now, generate mock embedding based on text hash
        return self._generate_mock_embedding(text)

    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for development."""
        import math

        # Create deterministic but varied embedding based on text
        text_hash = hashlib.md5(text.lower().encode()).hexdigest()
        embedding = []

        for i in range(0, min(len(text_hash) * 12, self.embedding_dimensions), 12):
            if i < len(text_hash):
                hex_val = int(text_hash[i % len(text_hash)], 16) / 15.0
            else:
                hex_val = 0.5

            # Create varied dimensions
            embedding.append(math.sin(hex_val * math.pi + i))
            embedding.append(math.cos(hex_val * math.pi + i))
            embedding.append(hex_val - 0.5)
            embedding.append((hex_val * 2) - 1)

        # Pad to correct dimensions
        while len(embedding) < self.embedding_dimensions:
            embedding.append(0.0)

        # Normalize
        magnitude = math.sqrt(sum(x**2 for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding[:self.embedding_dimensions]

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for keyword search."""
        # Simple tokenization - in production use proper NLP
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)

        # Remove stop words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "for", "and", "or", "but", "if", "then", "else",
            "when", "at", "by", "from", "with", "to", "of", "in", "on",
            "it", "its", "this", "that", "these", "those",
        }

        return [w for w in words if w not in stop_words and len(w) > 2]

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        words = self._tokenize(text)
        word_freq = defaultdict(int)

        for word in words:
            word_freq[word] += 1

        # Get top keywords by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:20]]

    async def search(
        self,
        tenant_id: str,
        query: SearchQuery,
    ) -> List[SearchResult]:
        """
        Search the knowledge base.

        Args:
            tenant_id: Tenant identifier
            query: Search query with filters

        Returns:
            List of SearchResult sorted by relevance
        """
        results: List[SearchResult] = []

        # Generate query embedding
        query_embedding = await self._generate_embedding(query.query)

        # Get candidate chunks
        candidate_chunk_ids = set()

        if query.use_semantic:
            # Get all chunks (in production, use ANN index)
            candidate_chunk_ids = set(self._chunks.keys())

        if query.use_keyword:
            # Keyword search using inverted index
            query_words = self._tokenize(query.query)
            for word in query_words:
                candidate_chunk_ids.update(self._inverted_index.get(word, []))

        # Score each candidate
        for chunk_id in candidate_chunk_ids:
            chunk = self._chunks.get(chunk_id)
            if not chunk:
                continue

            # Get document
            doc = self._documents.get(chunk.document_id)
            if not doc:
                continue

            # Filter by tenant
            if doc.tenant_id != tenant_id and doc.tenant_id != "default":
                continue

            # Apply filters
            if query.document_types and doc.document_type not in query.document_types:
                continue

            if query.specialties and doc.specialty not in query.specialties:
                continue

            if query.evidence_levels and doc.evidence_level not in query.evidence_levels:
                continue

            if query.condition_codes:
                if not any(code in doc.condition_codes for code in query.condition_codes):
                    continue

            if query.procedure_codes:
                if not any(code in doc.procedure_codes for code in query.procedure_codes):
                    continue

            # Calculate similarity score
            similarity_score = 0.0
            if query.use_semantic and chunk.embedding:
                similarity_score = self._cosine_similarity(
                    query_embedding,
                    chunk.embedding,
                )

            # Calculate keyword score
            keyword_score = 0.0
            if query.use_keyword:
                keyword_score = self._calculate_keyword_score(
                    query.query,
                    chunk.text,
                )

            # Combined score
            combined_score = (
                query.semantic_weight * similarity_score +
                (1 - query.semantic_weight) * keyword_score
            )

            # Filter by minimum similarity
            if combined_score < query.min_similarity:
                continue

            results.append(SearchResult(
                chunk_id=chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                similarity_score=similarity_score,
                keyword_score=keyword_score,
                combined_score=combined_score,
                document_title=doc.title,
                document_type=doc.document_type,
                metadata=chunk.metadata,
                specialty=doc.specialty,
                evidence_level=doc.evidence_level,
                source=doc.source,
            ))

        # Sort by combined score
        results.sort(key=lambda x: x.combined_score, reverse=True)

        # Rerank if enabled
        if query.rerank and len(results) > query.top_k:
            results = await self._rerank(query.query, results[:query.rerank_top_k])

        return results[:query.top_k]

    def _cosine_similarity(
        self,
        vec_a: List[float],
        vec_b: List[float],
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        import math

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = math.sqrt(sum(a * a for a in vec_a))
        magnitude_b = math.sqrt(sum(b * b for b in vec_b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return (dot_product / (magnitude_a * magnitude_b) + 1) / 2  # Normalize to 0-1

    def _calculate_keyword_score(
        self,
        query: str,
        text: str,
    ) -> float:
        """Calculate keyword match score (simplified BM25)."""
        query_words = set(self._tokenize(query))
        text_words = self._tokenize(text)

        if not query_words or not text_words:
            return 0.0

        # Count matches
        matches = sum(1 for word in text_words if word in query_words)

        # Normalize by query length and text length
        score = matches / (len(query_words) * (1 + len(text_words) / 100))
        return min(1.0, score * 2)  # Scale and cap at 1.0

    async def _rerank(
        self,
        query: str,
        results: List[SearchResult],
    ) -> List[SearchResult]:
        """Rerank results using cross-encoder or LLM."""
        # In production, use a cross-encoder model for reranking
        # For now, apply simple heuristics

        for result in results:
            boost = 0.0

            # Boost by evidence level
            if result.evidence_level == EvidenceLevel.LEVEL_A:
                boost += 0.1
            elif result.evidence_level == EvidenceLevel.LEVEL_B:
                boost += 0.05

            # Boost clinical guidelines
            if result.document_type == DocumentType.CLINICAL_GUIDELINE:
                boost += 0.05

            result.combined_score += boost

        # Re-sort
        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results

    async def build_rag_context(
        self,
        tenant_id: str,
        query: str,
        max_chunks: int = 5,
        max_tokens: int = 2000,
        document_types: Optional[List[DocumentType]] = None,
        specialties: Optional[List[str]] = None,
    ) -> RAGContext:
        """
        Build context for RAG (Retrieval-Augmented Generation).

        Args:
            tenant_id: Tenant identifier
            query: User query
            max_chunks: Maximum chunks to include
            max_tokens: Maximum tokens estimate
            document_types: Filter by document types
            specialties: Filter by specialties

        Returns:
            RAGContext with formatted context
        """
        # Search for relevant chunks
        search_query = SearchQuery(
            query=query,
            top_k=max_chunks,
            document_types=document_types,
            specialties=specialties,
            use_semantic=True,
            use_keyword=True,
        )

        results = await self.search(tenant_id, search_query)

        # Build context text
        context_parts = []
        sources = []
        total_chars = 0

        for i, result in enumerate(results):
            # Estimate tokens (rough: 4 chars per token)
            chunk_chars = len(result.text)
            if total_chars + chunk_chars > max_tokens * 4:
                break

            context_parts.append(f"[Source {i+1}: {result.document_title}]")
            context_parts.append(result.text)
            context_parts.append("")

            sources.append({
                "title": result.document_title,
                "source": result.source or "Knowledge Base",
                "document_type": result.document_type.value if result.document_type else None,
                "evidence_level": result.evidence_level.value if result.evidence_level else None,
            })

            total_chars += chunk_chars

        context_text = "\n".join(context_parts)

        return RAGContext(
            query=query,
            search_results=results,
            context_text=context_text,
            sources=sources,
            total_chunks=len(results),
            total_tokens_estimate=total_chars // 4,
        )

    async def get_document(
        self,
        document_id: str,
    ) -> Optional[MedicalDocument]:
        """Get a document by ID."""
        return self._documents.get(document_id)

    async def delete_document(
        self,
        document_id: str,
    ) -> bool:
        """Delete a document and its chunks."""
        doc = self._documents.get(document_id)
        if not doc:
            return False

        # Delete chunks
        for chunk in doc.chunks:
            self._chunks.pop(chunk.chunk_id, None)
            self._embeddings.pop(chunk.chunk_id, None)

            # Remove from inverted index
            words = self._tokenize(chunk.text)
            for word in words:
                if chunk.chunk_id in self._inverted_index.get(word, []):
                    self._inverted_index[word].remove(chunk.chunk_id)

        # Delete document
        del self._documents[document_id]

        logger.info(f"Deleted document {document_id}")
        return True

    async def list_documents(
        self,
        tenant_id: str,
        document_type: Optional[DocumentType] = None,
        specialty: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MedicalDocument]:
        """List documents with optional filters."""
        docs = [
            doc for doc in self._documents.values()
            if (doc.tenant_id == tenant_id or doc.tenant_id == "default")
            and (document_type is None or doc.document_type == document_type)
            and (specialty is None or doc.specialty == specialty)
        ]

        # Sort by indexed_at descending
        docs.sort(key=lambda x: x.indexed_at or x.created_at, reverse=True)

        return docs[offset:offset + limit]

    async def get_statistics(
        self,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        docs = [
            doc for doc in self._documents.values()
            if doc.tenant_id == tenant_id or doc.tenant_id == "default"
        ]

        by_type = defaultdict(int)
        by_specialty = defaultdict(int)
        by_evidence = defaultdict(int)

        total_chunks = 0
        for doc in docs:
            by_type[doc.document_type.value] += 1
            if doc.specialty:
                by_specialty[doc.specialty] += 1
            by_evidence[doc.evidence_level.value] += 1
            total_chunks += len(doc.chunks)

        return {
            "total_documents": len(docs),
            "total_chunks": total_chunks,
            "total_keywords": len(self._inverted_index),
            "by_type": dict(by_type),
            "by_specialty": dict(by_specialty),
            "by_evidence_level": dict(by_evidence),
            "embedding_dimensions": self.embedding_dimensions,
            "chunk_size": self.chunk_size,
        }


# Global vector search service instance
vector_search_service = VectorSearchService()
