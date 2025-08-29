from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import time
from typing import List

from app.core.config import settings
from app.models.schemas import IngestionResponse, ErrorResponse, ChunkRequest
from app.utils.file_processing import FileProcessor
from app.core.chunking import TextChunker
from app.core.embeddings import embedding_service
from app.core.vector_store import vector_store
from app.models.document_models import DocumentChunk
from app.core.metrics import track_document_processing
from loguru import logger
from uuid import uuid4

router = APIRouter()
file_processor = FileProcessor()

@router.post(
    "/ingest",
    response_model=IngestionResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
@track_document_processing("unknown")
async def ingest_document(
    file: UploadFile = File(...),
    chunk_params: ChunkRequest = None
):
    """
    Upload and process documents for ingestion into the RAG system.
    
    Supports PDF and TXT files. Files are chunked with configurable
    size and overlap parameters.
    """
    start_time = time.time()
    
    try:
        # Validate file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Determine file type and extract text
        file_type = file_processor.get_file_type(file.filename)
        
        if file_type == 'pdf':
            text = file_processor.extract_text_from_pdf(file_content)
        elif file_type == 'txt':
            text = file_processor.extract_text_from_txt(file_content)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type"
            )
        
        # Clean text
        cleaned_text = file_processor.clean_text(text)
        
        # Chunk text
        chunker_params = chunk_params.dict() if chunk_params else {}
        chunker = TextChunker(**chunker_params)
        chunks = chunker.sliding_window_chunk(cleaned_text)
        
        # Prepare chunks with metadata and embeddings, then store in vector DB
        document_id = uuid4()
        chunk_metadatas = []
        doc_chunks = []
        for idx, chunk_text in enumerate(chunks):
            metadata = {
                "document_id": str(document_id),
                "file_name": file.filename,
                "file_type": file_type,
                "chunk_index": idx
            }
            chunk_metadatas.append(metadata)
            doc_chunks.append(
                DocumentChunk(
                    document_id=document_id,
                    content=chunk_text,
                    metadata=metadata
                )
            )

        # Generate embeddings in batch
        embeddings = embedding_service.generate_embeddings([c.content for c in doc_chunks]) if doc_chunks else []
        for i, emb in enumerate(embeddings):
            doc_chunks[i].embedding = emb

        # Store in vector store
        if doc_chunks:
            vector_store.store_chunks(doc_chunks)

        processing_time = time.time() - start_time
 
        logger.info(f"Processed file {file.filename}: {len(chunks)} chunks created")
        
        return IngestionResponse(
            message="Document processed successfully",
            file_id=file.filename,  # Keep this
            file_name=file.filename,  # ADD THIS REQUIRED FIELD
            file_type=file_type,      # ADD THIS REQUIRED FIELD
            chunks_created=len(chunks),
            processing_time=round(processing_time, 2),
            metadata={"document_id": str(document_id)}  # Optional: additional metadata
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Value error processing file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error processing file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during file processing"
        )



@router.post("/ingest/batch", response_model=List[IngestionResponse])
async def ingest_batch_documents(
    files: List[UploadFile] = File(...),
    chunk_params: ChunkRequest = None
):
    """Process multiple documents in batch"""
    results = []
    
    for file in files:
        try:
            # We need to manually call the logic since we can't call ingest_document directly
            # due to the required fields issue
            start_time = time.time()
            
            file_content = await file.read()
            file_type = file_processor.get_file_type(file.filename)
            
            if file_type == 'pdf':
                text = file_processor.extract_text_from_pdf(file_content)
            elif file_type == 'txt':
                text = file_processor.extract_text_from_txt(file_content)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported file type"
                )
            
            cleaned_text = file_processor.clean_text(text)
            chunker_params = chunk_params.dict() if chunk_params else {}
            chunker = TextChunker(**chunker_params)
            chunks = chunker.sliding_window_chunk(cleaned_text)
            processing_time = time.time() - start_time
            
            results.append(IngestionResponse(
                message="Document processed successfully",
                file_id=file.filename,
                file_name=file.filename,
                file_type=file_type,
                chunks_created=len(chunks),
                processing_time=round(processing_time, 2)
            ))
            
        except HTTPException as e:
            # Continue processing other files even if one fails
            results.append(IngestionResponse(
                message=f"Failed to process {file.filename}",
                file_id=file.filename,
                file_name=file.filename,
                file_type="unknown",
                chunks_created=0,
                processing_time=0.0
            ))
        except Exception as e:
            results.append(IngestionResponse(
                message=f"Error processing {file.filename}: {str(e)}",
                file_id=file.filename,
                file_name=file.filename,
                file_type="unknown",
                chunks_created=0,
                processing_time=0.0
            ))
    
    return results