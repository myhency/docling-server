"""FastAPI application for document conversion service."""
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import UPLOAD_DIR, STATIC_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE
from app.converter import create_converter

# Create FastAPI app
app = FastAPI(
    title="Document Converter API",
    description="Convert office documents to Markdown with extracted figures",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Initialize converter
converter_service = create_converter()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Document Converter API",
        "version": "1.0.0",
        "endpoints": {
            "convert/with-images": "POST /convert/with-images - Convert document to Markdown with extracted images",
            "convert/markdown": "POST /convert/markdown - Convert document to Markdown only (no image extraction)",
            "convert": "POST /convert - Convert document to Markdown with extracted images (deprecated, use /convert/with-images)",
            "health": "GET /health - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "document-converter"}


async def _convert_document_helper(file: UploadFile, extract_images: bool) -> Dict[str, Any]:
    """
    Helper function to convert document with optional image extraction.

    Args:
        file: Uploaded document file
        extract_images: Whether to extract and save images

    Returns:
        JSON response dict

    Raises:
        HTTPException: If file validation fails or conversion errors occur
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique filename for temporary storage
    unique_id = str(uuid.uuid4())
    temp_filename = f"{unique_id}_{file.filename}"
    temp_file_path = UPLOAD_DIR / temp_filename

    try:
        # Save uploaded file
        with temp_file_path.open("wb") as buffer:
            content = await file.read()

            # Check file size
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds maximum allowed size of {MAX_UPLOAD_SIZE / 1024 / 1024}MB"
                )

            buffer.write(content)

        # Convert document
        try:
            markdown_content, figures_info = converter_service.convert_document(
                temp_file_path,
                file.filename,
                extract_images=extract_images
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Conversion failed: {str(e)}"
            )

        # Prepare response
        response = {
            "status": "success",
            "original_filename": file.filename,
            "markdown": markdown_content,
            "figures": figures_info,
            "figures_count": len(figures_info)
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file_path.exists():
            temp_file_path.unlink()


@app.post("/convert/markdown")
async def convert_markdown_only(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Convert uploaded document to Markdown format only (without image extraction).

    Args:
        file: Uploaded document file

    Returns:
        JSON response with markdown content only

    Raises:
        HTTPException: If file validation fails or conversion errors occur
    """
    response = await _convert_document_helper(file, extract_images=False)
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@app.post("/convert/with-images")
async def convert_with_images(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Convert uploaded document to Markdown format with extracted images.

    Args:
        file: Uploaded document file

    Returns:
        JSON response with markdown content and extracted figures information

    Raises:
        HTTPException: If file validation fails or conversion errors occur
    """
    response = await _convert_document_helper(file, extract_images=True)
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@app.post("/convert")
async def convert_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Convert uploaded document to Markdown format with extracted images.

    DEPRECATED: Use /convert/with-images instead.

    Args:
        file: Uploaded document file

    Returns:
        JSON response with markdown content and extracted figures information

    Raises:
        HTTPException: If file validation fails or conversion errors occur
    """
    response = await _convert_document_helper(file, extract_images=True)
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@app.delete("/figures/{figure_filename}")
async def delete_figure(figure_filename: str):
    """
    Delete a specific figure file.

    Args:
        figure_filename: Name of the figure file to delete

    Returns:
        Success message

    Raises:
        HTTPException: If file not found or deletion fails
    """
    figure_path = STATIC_DIR / "figures" / figure_filename

    if not figure_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Figure not found"
        )

    try:
        figure_path.unlink()
        return {"status": "success", "message": f"Figure {figure_filename} deleted"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete figure: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    from app.config import API_HOST, API_PORT

    uvicorn.run(
        "app.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
