import logging

from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer
from pydantic import BaseModel, Field

from ai_config.ai_constants import (
    EMBEDDING_CHUNK_SIZE,
    EMBEDDING_OVERLAP,
)

logger = logging.getLogger(__name__)

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")  # ou outro tokenizer

def token_length_function(text):
    return len(tokenizer.encode(text, truncation=False))



class BrainDocument:
    def __init__(self, page_content, metadata, id="0"):
        self.id = id
        self.page_content = page_content
        self.metadata = metadata

    def __str__(self):
        # Mostra o id e os primeiros 100 caracteres do conteúdo para não poluir o log
        return f"BrainDocument(id={self.id}, page_content={self.page_content[:100]}..., metadata={self.metadata})"
    
    # Text Splitter Class
class BrainTextSplitter(RecursiveCharacterTextSplitter):
    def __init__(
        self,
        chunk_size=EMBEDDING_CHUNK_SIZE,
        chunk_overlap=EMBEDDING_OVERLAP,
        length_function=token_length_function,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function

    def split_documents(self, documents):
        if not documents:
            return []

        chunks = []
       
        for doc in documents:
            try:
                metadata = {**(doc.metadata if isinstance(doc.metadata, dict) else {}), "id": getattr(doc, "id", "no_id")}
                text = doc.page_content
                intent = metadata.get("intent", "")
                
                text = f"[intent: {intent}]\n{text}" 
                id_doc = getattr(doc, "id", "no_id")
        
                # Handle short documents
                if self.length_function(text) <= self.chunk_size:
                    chunks.append(BrainDocument(id=id_doc,page_content=text, metadata=metadata))
                    continue

                # Split into sentences
                sentences = [s.strip() + ". " for s in text.split(". ") if s.strip()]
                current_chunk = []
                current_length = 0

                for sentence in sentences:
                    sentence_length = self.length_function(sentence)

                    # Handle sentences longer than chunk_size
                    if sentence_length > self.chunk_size:
                        if current_chunk:
                            chunks.append(
                                BrainDocument(
                                    id=id_doc,
                                    page_content="".join(current_chunk),
                                    metadata=metadata,
                                )
                            )
                            current_chunk = []
                            current_length = 0

                        # Split long sentence
                        words = sentence.split()
                        current_words = []
                        current_word_length = 0

                        for word in words:
                            word_length = self.length_function(word + " ")
                            if current_word_length + word_length > self.chunk_size:
                                chunks.append(
                                    BrainDocument(
                                        id=id_doc,
                                        page_content=" ".join(current_words),
                                        metadata=metadata,
                                    )
                                )
                                current_words = [word]
                                current_word_length = word_length
                            else:
                                current_words.append(word)
                                current_word_length += word_length

                        if current_words:
                            current_chunk = [" ".join(current_words)]
                            current_length = self.length_function(current_chunk[0])
                        continue

                    # Normal sentence processing
                    if current_length + sentence_length > self.chunk_size:
                        if current_chunk:
                            chunks.append(
                                BrainDocument(
                                    id=id_doc,
                                    page_content="".join(current_chunk),
                                    metadata=metadata,
                                )
                            )

                            # Handle overlap
                            overlap_start = max(
                                0, len(current_chunk) - self.chunk_overlap
                            )
                            current_chunk = current_chunk[overlap_start:]
                            current_length = sum(
                                self.length_function(s) for s in current_chunk
                            )

                    current_chunk.append(sentence)
                    current_length += sentence_length

                # Add remaining text
                if current_chunk:
                    chunks.append(
                        BrainDocument(
                            id=id_doc,
                            page_content="".join(current_chunk),
                            metadata=metadata
                        )
                    )
            except Exception as e:
                logger.error(f"Error splitting document: {str(e)}")
                continue
        return chunks
    
    # Define grading of docs
class GradeDocuments(BaseModel):
    confidence_score: float = Field(
        description="Confidence score between 0.0 and 1.0 indicating document relevance",
        ge=0.0,
        le=1.0,
    )
    
# Define GradeHallucinations Model
class GradeConfidenceLevel(BaseModel):
    confidence_score: float = Field(
        description="""Confidence score between 0.0 and 1.0
        indicating how well the answer is grounded in source facts""",
        ge=0.0,
        le=1.0,
    )